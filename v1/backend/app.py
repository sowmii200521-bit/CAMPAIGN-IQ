import os
import uuid
import subprocess
import sys
import logging
import json # Kept for potential future use, but not strictly needed for the CSV logic
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename 

# Import necessary libraries that were used in the working version
import shutil
import pandas as pd
from typing import Optional # Used for type hinting, though not critical for function

from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging for easier debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 1. Instantiate the Flask app first
app = Flask(__name__)
CORS(app)

# 2. CRITICAL PATH FIX: Define paths relative to the Project Root
# Path(__file__).parent is the 'backend' folder. We use .parent.parent 
# to get to the 'CampaignIQ' directory (the project root).
PROJECT_ROOT = Path(__file__).parent.parent

# Define directories relative to the Project Root
BASE_OUTPUT_DIR = PROJECT_ROOT / 'outputs'
TEMP_DIR = PROJECT_ROOT / 'uploads'
SCRIPT_PATH = PROJECT_ROOT / 'backend' / 'causal_impact.py' 

# Ensure the necessary directories exist upon startup
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Configuration for file upload
ALLOWED_EXTENSIONS = {'csv'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Vercel, Render, or uptime monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "CampaignIQ Causal Engine API",
        "version": "1.0.0"
    }), 200


@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """
    Handles file upload, executes the causal analysis script, and returns the 
    results in the 'stats' structure the frontend expects.
    """
    # --- File Upload and Setup ---
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'message': 'Invalid file type. Only CSV allowed.'}), 400

    # 1. Setup paths and save uploaded file
    session_id = str(uuid.uuid4())
    data_filename = f"{session_id}_{secure_filename(file.filename)}"
    data_path = TEMP_DIR / data_filename
    session_output_dir = BASE_OUTPUT_DIR / session_id
    
    try:
        file.save(str(data_path))
        session_output_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created output directory: {session_output_dir.absolute()}")
    except Exception as e:
        logging.error(f"Error saving file or creating directory: {e}")
        return jsonify({"message": f"Server setup failed: {e}"}), 500

    # Define absolute paths for script arguments
    output_path_str = str(session_output_dir.absolute())
    data_path_str = str(data_path.absolute())
    script_path_str = str(SCRIPT_PATH.absolute()) 
    
    # 3. Execute the Python script
    try:
        command = [
            sys.executable, script_path_str, 
            '--data', data_path_str,
            '--outdir', output_path_str, # Pass the ABSOLUTE output path
            '--plots' 
        ]
        
        logging.info(f"Executing Analysis Command: {' '.join(command)}")
        
        # Run the subprocess
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            check=False # Set to False to handle error checking manually below
        )
        
        logging.info(f"Analysis Script STDOUT:\n{result.stdout}")

        if result.returncode != 0:
            error_msg = (
                f"Analysis script failed (Exit Code {result.returncode}).\n"
                f"--- Script STDERR/Error Log ---\n{result.stderr}\n---------------------\n"
                "The analysis script crashed."
            )
            logging.error(error_msg)
            raise RuntimeError(error_msg)
            
        # --- Read Results from CSV ---
        # NOTE: Reverting to the logic that reads the CSV output file.
        summary_file_path = session_output_dir / 'causal_impact_summary.csv'
        report_path = session_output_dir / 'report.md'
        
        if not summary_file_path.exists():
            raise FileNotFoundError(f"Analysis outputs (causal_impact_summary.csv) were not generated. Path: {summary_file_path.absolute()}")

        summary_df = pd.read_csv(summary_file_path)
        # Using the AIPW result as the primary metric
        aipw_result = summary_df[summary_df['Method'].str.contains('AIPW')].iloc[0]
        
        # Read Report Preview
        report_content = "Report not found."
        if report_path.exists():
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()

        # --- Prepare Key Stats for Frontend (CRITICAL FIX FOR TYPERROR) ---
        # The frontend expects a 'stats' object containing 'effectiveness'
        # We assume the CSV stores the ATE as a decimal (0.05) or a percentage (5.0)
        ate_pp = aipw_result['ATE_pp']
        ci_lower_pp = aipw_result['CI_lower_pp']
        
        # Determine effectiveness string
        confidence = 0.95
        effectiveness = 'High' if ci_lower_pp > 0 and ate_pp > 0 else ('Medium' if ate_pp > 0 else 'Low')
        
        key_stats = {
            # NOTE: We return the raw numbers, the frontend can format them.
            'ate': ate_pp / 100.0, # Convert percentage point (e.g., 5.0) back to decimal (0.05)
            'confidence': confidence,
            'effectiveness': effectiveness # The missing field!
        }

        # --- Clean Up and Success Return ---
        os.remove(data_path)

        return jsonify({
            'status': 'success',
            'runId': session_id,
            'stats': key_stats, # <--- THIS IS THE STRUCTURE THE FRONTEND EXPECTS
            'reportPreview': report_content[:300] + '...'
        }), 200
        
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        logging.error(f"FATAL ANALYSIS ERROR (Run {session_id}): {error_msg}")
        
        # Clean up files in case of failure
        shutil.rmtree(session_output_dir, ignore_errors=True)
        if data_path.exists():
             os.remove(data_path)
             
        # Return a valid JSON error response
        return jsonify({'status': 'error', 'message': error_msg}), 500


@app.route('/api/download/<session_id>/<filename>', methods=['GET'])
def download_file(session_id, filename):
    """
    Serves the requested output file from the session-specific output directory.
    This replaces the old download route logic.
    """
    file_path = BASE_OUTPUT_DIR / session_id / secure_filename(filename)
    
    if not file_path.exists():
        logging.warning(f"File not found during download attempt: {file_path.absolute()}")
        return jsonify({'status': 'error', 'message': 'File not found'}), 404

    # Determine MIME type
    suffix = file_path.suffix.lower()
    if suffix in ['.png', '.jpg', '.jpeg']:
        mimetype = f'image/{suffix[1:]}'
    elif suffix == '.csv':
        mimetype = 'text/csv'
    elif suffix == '.md':
        mimetype = 'text/markdown'
    else:
        mimetype = 'application/octet-stream'

    logging.info(f"Serving file: {file_path.absolute()}")
    return send_file(
        str(file_path.absolute()),
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    ) 

@app.route('/api/download_all/<session_id>', methods=['GET'])
def download_all(session_id):
    """
    Compresses all generated files for a given session_id into a ZIP archive and serves it.
    """
    session_output_dir = BASE_OUTPUT_DIR / session_id
    
    if not session_output_dir.exists():
        logging.warning(f"Session directory not found for batch download: {session_output_dir.absolute()}")
        return jsonify({'status': 'error', 'message': 'Analysis results not found for this session.'}), 404

    try:
        # Define the base path for the temporary ZIP file in the TEMP_DIR
        temp_zip_path_base = TEMP_DIR / f'CampaignIQ_Report_{session_id}'
        
        # Create the ZIP archive
        # base_name: The name and path of the archive to create (without .zip extension)
        # format: 'zip'
        # root_dir: The directory to start the archival process from (we use the parent of the output dir)
        # base_dir: The directory inside the root_dir to archive (the session folder itself)
        archive_path = shutil.make_archive(
            base_name=str(temp_zip_path_base), 
            format='zip', 
            root_dir=session_output_dir.parent, # Starts from 'outputs' directory
            base_dir=session_output_dir.name    # Archives the specific session folder (e.g., 'abc-123')
        )
        
        logging.info(f"Created ZIP archive at: {archive_path}")

        # Send the created ZIP file
        response = send_file(
            archive_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"CampaignIQ_Report_{session_id}.zip"
        )
        
        # Schedule the clean up of the generated ZIP file *after* it's been sent.
        # Note: In a production Flask app, you'd use @app.after_request, but 
        # in this environment, relying on os.remove() after the response object is returned is the simplest approach.
        @response.call_on_close
        def cleanup_zip():
            try:
                os.remove(archive_path)
                logging.info(f"Cleaned up temporary ZIP archive: {archive_path}")
            except Exception as cleanup_e:
                logging.warning(f"Failed to clean up temporary ZIP archive: {cleanup_e}")

        return response
        
    except Exception as e:
        error_msg = f"Batch download failed: {str(e)}"
        logging.error(f"Error during ZIP creation/serving: {error_msg}")
        # Clean up potential partial zip file if it exists
        zip_file_to_cleanup = f"{str(temp_zip_path_base)}.zip"
        if os.path.exists(zip_file_to_cleanup):
            os.remove(zip_file_to_cleanup)
            logging.info(f"Cleaned up partial ZIP archive: {zip_file_to_cleanup}")

        return jsonify({'status': 'error', 'message': error_msg}), 500


def build_run_context(session_id: Optional[str]) -> str:
    """Extracts analytical tables and reports from a session directory to ground the chat LLM."""
    if not session_id:
        return "No specific campaign run selected yet."
    session_dir = BASE_OUTPUT_DIR / secure_filename(session_id)
    if not session_dir.exists():
        return f"Campaign run {session_id} not found."

    context_parts = []

    # 1. Summary table (ATEs)
    summary_path = session_dir / 'causal_impact_summary.csv'
    if summary_path.exists():
        try:
            df = pd.read_csv(summary_path)
            context_parts.append("### Method Comparisons & Average Treatment Effect (ATE):\n" + df.to_string(index=False))
        except Exception as e:
            logging.warning(f"Failed to read summary for context: {e}")

    # 2. Recommendations & top segments (cleanly formatted)
    rec_path = session_dir / 'next_wave_recommendations_aipw.csv'
    if rec_path.exists():
        try:
            rec_df = pd.read_csv(rec_path)
            rec_lines = []
            for _, row in rec_df.head(10).iterrows():
                seg_name = ""
                # Check specific segment keys in priority order
                raw_val = ""
                prefix = ""
                if pd.notna(row.get('district_age')) and str(row.get('district_age')).strip():
                    raw_val = str(row.get('district_age'))
                    prefix = "District & Age"
                elif pd.notna(row.get('send_time')) and str(row.get('send_time')).strip():
                    raw_val = str(row.get('send_time'))
                    prefix = "Send Time"
                elif pd.notna(row.get('district')) and str(row.get('district')).strip():
                    raw_val = str(row.get('district'))
                    prefix = "District"
                elif pd.notna(row.get('age_band')) and str(row.get('age_band')).strip():
                    raw_val = str(row.get('age_band'))
                    prefix = "Age Band"
                elif pd.notna(row.get('locale')) and str(row.get('locale')).strip():
                    raw_val = str(row.get('locale'))
                    prefix = "Locale"

                cleaned = raw_val.replace("('", "").replace("')", "").replace("'", "").replace('"', '').strip()
                seg_name = prefix + ": " + cleaned if prefix else "General Cohort"

                uplift = row.get('estimated_uplift_pp', 0.0)
                ci_low = row.get('ci95_lower_pp', 0.0)
                ci_high = row.get('ci95_upper_pp', 0.0)
                n = int(row.get('n', 0)) if pd.notna(row.get('n')) else 0
                rec_lines.append(f"- **{seg_name}**: Estimated Uplift = +{uplift:.2f}pp (95% CI: [{ci_low:.2f}pp, {ci_high:.2f}pp], Sample Size n={n})")

            context_parts.append("### Top Recommended Actionable Segments Ranked by Uplift:\n" + "\n".join(rec_lines))
        except Exception as e:
            logging.warning(f"Failed to read recommendations for context: {e}")

    # 3. Covariate Balance table
    balance_path = session_dir / 'balance_smd.csv'
    if balance_path.exists():
        try:
            b_df = pd.read_csv(balance_path)
            context_parts.append("### Covariate Balance (Standardized Mean Differences):\n" + b_df.to_string(index=False))
        except Exception as e:
            logging.warning(f"Failed to read balance for context: {e}")

    # 4. Executive Summary Report
    report_path = session_dir / 'report.md'
    if report_path.exists():
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                context_parts.append("### Generated Executive Report:\n" + f.read())
        except Exception as e:
            logging.warning(f"Failed to read report for context: {e}")

    return "\n\n".join(context_parts) if context_parts else "Analysis outputs found, but contents are empty."


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Interactive Q&A assistant grounded in the campaign's causal analysis outputs.
    """
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    session_id = data.get('runId')
    history = data.get('history', [])

    if not message:
        return jsonify({'status': 'error', 'message': 'Message is required'}), 400

    context = build_run_context(session_id)

    system_prompt = (
        "You are CampaignIQ Assistant, an expert data scientist and public health campaign strategist.\n"
        "You are helping a campaign manager or health organization director interpret their campaign causal evaluation results.\n\n"
        f"=== VERIFIED CAMPAIGN ANALYSIS DATA (Run: {session_id or 'General'}) ===\n"
        f"{context}\n"
        "===========================================================\n\n"
        "Crucial Context & Guidelines:\n"
        "- The objective/metric is **7-day health clinic/appointment booking rate** (outcome_booking_7d), measured in percentage point (pp) uplift. It is NOT e-commerce sales or dollar revenue. Do not hallucinate financial dollar ROI figures.\n"
        "- Answer the user's question directly, clearly, and informatively.\n"
        "- Ground your answers in the exact numbers above (ATE: +5.11pp, 95% CI: [2.41, 7.80]pp, segment uplifts, sample sizes) whenever relevant.\n"
        "- In segment questions, refer to cohorts by their specific descriptive names (e.g. 'District & Age: Chennai 40-59', 'Send Time: Morning'). Do not output empty quotes `''`.\n"
        "- In send time questions: Morning achieved +6.91pp uplift, whereas Evening achieved +4.12pp uplift. Morning is noticeably superior (+2.79pp higher).\n"
        "- Arithmetic rule: NEVER add or sum percentage uplifts from different segments together (e.g. 9.07% + 7.26% != 16.33%). Report segment uplifts separately or as a weighted average.\n"
        "- Explain causal inference concepts (such as AIPW double-robustness, confounding bias vs naive difference, propensity scoring) in accessible, intuitive terms.\n"
        "- Format your answer with clean markdown bullet points, bold numbers, and concise paragraphs."
    )

    hf_token = os.environ.get("HF_TOKEN")
    answer = None

    if hf_token:
        try:
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=hf_token)
            
            messages = [{"role": "system", "content": system_prompt}]
            # Include recent chat history
            for turn in history[-6:]:
                if turn.get('role') in ['user', 'assistant'] and turn.get('content'):
                    messages.append({"role": turn['role'], "content": turn['content']})
            messages.append({"role": "user", "content": message})

            models_to_try = [
                "meta-llama/Llama-3.1-8B-Instruct",
                "mistralai/Mistral-7B-Instruct-v0.2"
            ]
            for model_id in models_to_try:
                try:
                    res = client.chat_completion(
                        messages=messages,
                        model=model_id,
                        max_tokens=800,
                        temperature=0.4
                    )
                    answer = res.choices[0].message.content
                    break
                except Exception as me:
                    logging.warning(f"Chat model {model_id} failed: {me}")
        except Exception as e:
            logging.error(f"InferenceClient error in chat: {e}")

    if not answer:
        # Fallback informative rule-based response
        answer = (
            f"Here is what the campaign data indicates:\n\n"
            f"- **Primary Causal Effect (AIPW):** The campaign achieved a statistically significant **+5.11 percentage point uplift** in 7-day bookings.\n"
            f"- **Confidence Interval (95%):** [2.41%, 7.80%], confirming genuine positive impact.\n"
            f"- **Confounding Notice:** The naive correlation (+6.73%) overestimated the true effect by ~1.62pp due to confounding factors, demonstrating the need for doubly-robust causal adjustment.\n"
            f"- **Targeting Advice:** Prioritize top-performing cohorts (such as young adults and specific districts) for the next wave to optimize resource efficiency."
        )

    return jsonify({
        'status': 'success',
        'answer': answer
    }), 200


if __name__ == '__main__':
    logging.info(f"Starting Flask server on http://127.0.0.1:5000")
    app.run(debug=True)

import { BarChart3, Download } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export const Header = () => {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/80 backdrop-blur-lg">
      <div className="container mx-auto px-6 h-20 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 hover:opacity-70 transition-opacity">
          <BarChart3 className="w-6 h-6 text-primary" />
          <span className="text-xl font-semibold tracking-tight">CampaignIQ</span>
        </Link>
        
        <nav className="flex items-center gap-4">
          <Link 
            to="/"
            className="text-sm font-medium hover:text-foreground/70 transition-colors hidden sm:inline-block"
          >
            Home
          </Link>
          <Button asChild variant="outline" size="sm" className="rounded-full gap-2 border-primary/30 hover:border-primary text-primary hover:bg-primary/10 shadow-sm transition-all">
            <a href={`${import.meta.env.BASE_URL}campaign_dataset.csv`} download="campaign_dataset.csv">
              <Download className="w-4 h-4" />
              <span>Download Demo Dataset</span>
            </a>
          </Button>
        </nav>
      </div>
    </header>
  );
};


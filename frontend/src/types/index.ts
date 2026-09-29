export interface Listing {
  id: string;
  url: string;
  title: string;
  price: number | string | null;
  currency: string;
  location: string | null;
}

export interface AlertRule {
  id: string;
  name: string;
  keywords: string | null;
  max_price: number | string | null;
  location: string | null;
  is_active: boolean;
}

export interface ListingStats {
  total: number;
  active: number;
  avg_price: number | null;
}

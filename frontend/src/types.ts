export interface StationEntry {
    name: string;
    station_id: string;
    state: string;
    elevation_m: number;
    value: number;
    all_time_max?: number;
    all_time_min?: number;
    all_time_max_year?: number;
    all_time_min_year?: number;
    hist_mean_swe?: number;
    current_swe?: number;
    data_date?: string;
}

export interface CategoryData {
    top: StationEntry[];
    bottom: StationEntry[];
    total_count: number;
    notes?: string;
}

export interface LeaderboardMetadata {
    generated_at: string;
    max_date: string;
    min_date: string;
    total_stations: number;
}

export interface LeaderboardData {
    metadata: LeaderboardMetadata;
    [key: string]: CategoryData | LeaderboardMetadata;
}

export type CategoryFilter = 'all' | 'snow' | 'swe' | '24h' | '48h' | '7d' | 'historical';

export interface MetricConfig {
    id: string;
    title: string;
    icon: string;
    desc: string;
    type: 'snow' | 'swe' | 'elevation' | 'zscore';
    showAllTime?: boolean;
    filters: CategoryFilter[];
}

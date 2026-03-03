export interface StationEntry {
    station_id: string;
    name: string;
    state: string;
    elevation_m: number;
    value: number;
    data_date?: string;
    all_time_max?: number;
    all_time_min?: number;
    all_time_max_year?: number;
    all_time_min_year?: number;
    current_swe?: number;
    hist_mean_swe?: number;
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


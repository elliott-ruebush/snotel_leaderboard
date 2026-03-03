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

export function convert(val: number | null | undefined, type: 'snow' | 'swe' | 'elevation' | 'zscore', targetUnit: 'metric' | 'imperial'): number | null {
    if (val === null || val === undefined) return null;
    if (targetUnit === 'metric') return val;

    if (type === 'snow' || type === 'swe') {
        return val * 39.3700787; // meters to inches
    }
    if (type === 'elevation') {
        return val * 3.28084; // meters to feet
    }
    return val;
}

export function getSuffix(type: 'snow' | 'swe' | 'elevation' | 'zscore', unit: 'metric' | 'imperial'): string {
    if (type === 'zscore') return '';
    if (unit === 'metric') return ' m';
    return type === 'elevation' ? ' ft' : ' in';
}

export function stationUrl(stationId: string): string {
    const siteNum = stationId.split('_')[0];
    return `https://wcc.sc.egov.usda.gov/nwcc/site?sitenum=${siteNum}`;
}

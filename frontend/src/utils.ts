export function convert(val: number | null | undefined, type: 'snow' | 'swe' | 'elevation' | 'zscore', targetUnit: 'metric' | 'imperial'): number | null {
    if (val === null || val === undefined) return null;

    if (targetUnit === 'metric') {
        if (type === 'snow' || type === 'swe') return val * 100; // meters to cm
        return val; // meters
    }

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
    if (unit === 'metric') {
        return (type === 'snow' || type === 'swe') ? ' cm' : ' m';
    }
    return type === 'elevation' ? ' ft' : ' in';
}

export function stationUrl(stationId: string): string {
    const siteNum = stationId.split('_')[0];
    return `https://wcc.sc.egov.usda.gov/nwcc/site?sitenum=${siteNum}`;
}

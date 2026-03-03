import { describe, it, expect } from 'vitest'
import { convert, getSuffix, stationUrl } from './utils'

describe('SNOTEL Utils', () => {
    describe('convert', () => {
        it('should return cm for snow/swe in metric mode', () => {
            expect(convert(1, 'snow', 'metric')).toBe(100)
            expect(convert(1, 'swe', 'metric')).toBe(100)
        })

        it('should return meters for elevation in metric mode', () => {
            expect(convert(1000, 'elevation', 'metric')).toBe(1000)
        })

        it('should convert meters to inches for snow/swe', () => {
            const val = convert(1, 'snow', 'imperial')
            expect(val).toBeCloseTo(39.37, 2)
        })

        it('should convert meters to feet for elevation', () => {
            const val = convert(1, 'elevation', 'imperial')
            expect(val).toBeCloseTo(3.28084, 4)
        })

        it('should handle null values', () => {
            expect(convert(null, 'snow', 'imperial')).toBe(null)
            expect(convert(undefined, 'snow', 'imperial')).toBe(null)
        })
    })

    describe('getSuffix', () => {
        it('should return cm for metric snow/swe', () => {
            expect(getSuffix('snow', 'metric')).toBe(' cm')
            expect(getSuffix('swe', 'metric')).toBe(' cm')
        })

        it('should return m for metric elevation', () => {
            expect(getSuffix('elevation', 'metric')).toBe(' m')
        })

        it('should return in for imperial snow', () => {
            expect(getSuffix('snow', 'imperial')).toBe(' in')
        })

        it('should return ft for imperial elevation', () => {
            expect(getSuffix('elevation', 'imperial')).toBe(' ft')
        })
    })

    describe('stationUrl', () => {
        it('should parse station ID and return correct URL', () => {
            expect(stationUrl('679_WA_SNTL')).toBe('https://wcc.sc.egov.usda.gov/nwcc/site?sitenum=679')
        })
    })
})

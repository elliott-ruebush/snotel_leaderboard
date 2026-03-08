# Prios
1. (WIP) Move quality control into a central place in snotel_lib. Make it so that derived metrics can confidently perform just their core operations and know that data has either been filtered or flagged as inaccurate. Optional param to include or exclude flagged values?
  * For simple derived metrics like day-over-day snow depth change - we can just flag that the result itself seems like an outlier
  * For more complex historical metrics (like consistency of snow depth), we could perhaps paramtrize the number of years of historical data you require. Can we connect this to having robust metadata so that the metric calculation can defer to the metadata layer?
2. Explore additional historical metrics and analysis
3. Explore geospatial visualization of stations

# Structural thoughts
There are a few different themes I'm thinking about
* Data ingestion and cleaning - standardizing format, schema, and flagging/filtering bad values
* Derived computations (could be from historical or live data) for trends, metrics, and other interesting bits of analysis
* Displaying most recent readings and the "live leaderboard" aspect
* Archiving clean, standardized, historical data for future derived computations

It feels like there should be abstraction layers around each of the above concepts.

The first step is defining a layer where we standardize data format. This should be the "edge" of our system. We could bring data in from various upstream sources, but should ensure that we have it cleaned before attempting to do fruther calculations.

Everything else is easier to reason about and iterate on once we have a robust input layer.

snotel_lib (or perhaps a new name) should provide this standardization layer. However, we should also explore making this a very lightweight wrapper around some sort of preexisting solution for aggregating data from various sources rather than trying to reinvent the wheel or solve the problem on my own. If I want more flexible output options, perhaps we could add that to an existing library?

The quality control aspect is an important point here that may be the main source of logic in snotel_lib. As far as I'm aware, many data aggregation libraries are not attempting to clean the data and passing it through as is from original sources.

snotel_metrics should provide a robust set of tooling for derived calculations that operate on this standard data format and let us easily view trends in the data. Some of this functionality could perhaps be integrated into an upstream library or a MetPy/xclim? (Currently the logic lives in the snotel_leaderboard repo and should be moved out)

High-level module structure (should generously split logic within submodules to maintain readability and clarity)
src/snotel_lib
- data (used for the external input interfacing, houses schema definition for common formatting as well)
- clean (used for logic around data cleaning and quality control)
- calculation (used for computing actual derived metrics)
There should be a core function using data and clean to get nice datasets that a user can then use calculation on or do their own thing

tests
- data
- clean
- calculation

# Potential future improvements

## Source Data (snotel_lib)
Explore broader libraries as alternatives to Eric Gagliano's GitHub repo.
* metloom - https://github.com/M3Works/metloom
* ulmo - https://github.com/ulmo-dev/ulmo - seems to no longer be actively maintained
* Synoptic API - https://synopticdata.com/weatherapi/

### Data liveliness
How lively can we get?

For the github actions pipeline, we likely don't want to go truly live, but could explore more dynamic updates as part of a more robust frontend/backend split

### Consider integrating more sources beyond SNOTEL (Canadian + California specific sources)
Will need to handle different formats here. Maintain common data format after snotel_lib processing to make data usage simpler

## unit conversions (snotel_lib + snotel_leaderboard)
Convert all sensor measurements to metric and all datetime types to UTC

Robust switching between units for the frontend (For converting small numbers of values (like top/bottom of leaderboard) we can just do on the frontend)

## Dynamic data fetching (snotel_leaderboard)
Update the architecture to have a properly running frontend and backend so that users can dynamically query, filter, sort ranges of data in the leaderboards
* Spatial filtering
* Value-based filtering
* Temporal filtering

## Archiving Historical Data (independent venture?)
We can run a batch job to gen and backfill daily historical snapshots. Would neeed a database to store them at (although perhaps could explore using a github repo as a flat data store of daily data since there are only ~hundreds of stations). Compressed Parquet most efficient or is there a stronger format? Could do some profiling here.
* Look at Geoparquet IO - https://geoparquet.io/ + geoparquet more broadly. https://parquet.apache.org/blog/2026/02/13/native-geospatial-types-in-apache-parquet/
* Think about schemas and organization and providing self-documenting context to make it easy to use for human + LLM
* If we get nice, clean data, can we host this online somewhere/somehow? Earthmover marketplace? CUAHSI?

## Quality Control
### Flag or filter outliers or improbable data values (snotel_lib)
* Spatial quality control - do I reasonably match nearby stations? This is a flagging kind of variable since you could feasibly have drastically different values even at nearby stations due to wind transport, different aspects, hyper-local weather systems, etc.
* Temporal quality control - do I closely match previous days? Is the delta over time larger than expected? We could use bounding ranges for sensible values here as well. e.g. I wouldn't ever expect to have 20m snow depth or 5m of snow in a day. Need to decide on exact values that make sense here.
* Generate historical metadata for each station showing the absolute maximum and minimum values from all time for various measures. We should flag on values that exceed the maximum or the minimum (with a floor in the minimum case too)

#### Physical sensibility in relationships between variables (snotel_lib)

SWE > Snow depth not possible.

Precip accumulation should be in line with SWE and snow depth (need to further investigate how precip accumulation is calculated). SWE and snow depth should roughly match up. 

Use a bounding range on reasonable snow densities - both for fresh and overall snow dpeth? https://avalanche.org/avalanche-encyclopedia/weather/snow-ratio/

### Display quality control info (snotel_leaderboard)
Clearly display warnings on improbable or flagged data points (e.g. 2026-03-06 Casper Mtn SNOTEL snow depth reading that spiked up drastically, potentially due to some sensor error or interference?)

Brief section written up with details on the data filtering?

## GeoSpatial visualization
Display locations of stations and allow exploring their live + historical metadata

Take point geometry and display station location on some sort of map - can statically gen on the backend as an image asset to start? If moving more dynamic, may want to explore a more robust geospatial plotting library

## More in depth historical analysis (snotel_lib + snotel_leaderboard)
* Historical trends in SWE, Snow Depth, precip consistency.

* Snow Storage Index (https://www.nature.com/articles/s43247-023-00751-3), can canonically calculate it for previous water years and provide some sort of estimate/metric for how this year might compare?

* A more robust way to look at "interesting" values. e.g. I don't care as much about below average SWE by z-score for a station that normally gets a max of 5cm of SWE per year as I do for a station with 100cm of SWE that is now at 10cm for the same date. Some of this is going to have to be a heuristic or perhaps a user controlled parameter to determine how aggressively one filters out smaller scale stations. ## Data Source Migration
See `snotel_lib/DATA_SOURCE_MIGRATION.md` for Gemini's discussion and notes on potential alternatives to the current egagli dataset.

# MixShift Dashboard Notes

## Project Overview

The MixShift dashboard is designed to help actuaries quickly identify if mix shifts are driving trends in triangles across three different mix types:
1. Snapshot Date Mix - How distributions change between two Snapshot Dates
2. Earn Month Mix - How distributions change between two Earn Months
3. Join Month Mix - How distributions change between two Join Months

## Key Concepts

### Mix Type
Refers to the time dimension being analyzed:
- **Snapshot Date** - Analysis based on specific snapshot dates
- **Join Month** - Analysis based on when members joined
- **Earn Month** - Analysis based on when points were earned

### Mix Weight
The weight used to measure distributions varies by mix type:
- **Snapshot Date Mix** - Can use member counts or outstanding points
- **Earn Month Mix** - Primarily uses earned points
- **Join Month Mix** - Primarily uses member count

### KL Divergence
A statistical measure that quantifies how different two distributions are. Higher values indicate greater differences between distributions. Used to rank characteristics by the magnitude of their mix shift.

### Segments
Subsets of data for more focused analysis:
- **Snapshot Date Mix** - Clusters or Manual Dimensions
- **Earn Month Mix** - Earn Types
- **Join Month Mix** - Join Channels

## Dashboard Components

### Required Top Bar Components
1. **Dataset Selector** - For choosing which dataset to analyze
2. **Mix Type Display** - Shows the type of mix analysis (read-only, determined by dataset)
3. **Date 1 & Date 2** - Date selectors with labels that change based on mix type
4. **Weight Selector** - Dropdown for selecting the weight measure (options vary by mix type)
5. **Segment Bubbler** - For filtering to specific segments
6. **Variable Bubbler** - For selecting characteristics to analyze
7. **Histogram/Mix Toggle** - Switches between histogram view and 100% stacked chart view

### Data Visualization Components
1. **Segment Bubbler** - Shows unique combinations of segment variables
2. **Variable Bubbler** - Lists characteristics ranked by KL Divergence
3. **Histogram/Stacked Chart** - Shows distribution comparison between dates

#### Bubbler Components
Both bubblers are implemented using a modular design pattern with the AG-Grid component for interactive data display. The implementation is in `utils/bubbler_functions.py`.

1. **Segment Bubbler**
   - Purpose: Shows unique combinations of segment variables with their weights
   - Structure:
     ```
     <Segments> | <Weight Value>
     ```
   - Data Query:
     ```sql
     SELECT 
         <Segment Vars>,
         SUM(<weight>) as weight
     FROM <table_path>
     GROUP BY <Segment Vars>
     ```
   - Features:
     - Displays all unique values from the Segments dictionary
     - Allows filtering to specific subsets of each Segment
     - Weight values update based on selected weight measure
     - Implements smooth scrolling for long lists
     - Shows placeholder message when no segments are selected
     - Provides visual feedback during loading states
     - Supports multiple row selection

2. **Variable Bubbler**
   - Purpose: Lists characteristics ranked by KL Divergence
   - Structure:
     ```
     Variable | KL Divergence
     ```
   - Features:
     - Sorted by KL Divergence value (highest to lowest)
     - KL Divergence is calculated across all buckets for each variable
     - Provides visual indicators for divergence magnitude
     - Implements smooth scrolling for long variable lists
     - Shows placeholder message when no variables are selected
     - Provides loading indicators during calculations
     - Supports single row selection

## Data Structure

### Table Structure
The data consists of two categories of tables:
1. **Labels** - Lists all possible levels for each characteristic
2. **Data** - Summarizes distributions across characteristics

### Key Structure
Data tables are keyed by:
- Segment Variables (can be multiple)
- Time Variable (snapshot date, earn month, or join month)
- Characteristic
- Level

### Table Naming Conventions
Tables follow a consistent naming pattern to enable automatic metadata discovery:

#### Base Data Tables
Format: `{model}__mix__{version}__{date}__{time}`

Examples:
- `snapshot__mix__1__20240331__123456` - Snapshot Date Mix table
- `earn__mix__1__20240331__123456` - Earn Month Mix table
- `join__mix__1__20240331__123456` - Join Month Mix table

#### Schema Tables
Format: `{model}__mix__{version}__{date}__{time}__schema__1`

The schema tables contain metadata about their corresponding data tables. They are differentiated by the `__schema__1` suffix.

### Mix Type Mapping
Mix types are determined from the model prefix in the table name:
- `snapshot` or `tml5` → "Snapshot Date"
- `earn` → "Earn Month"
- `join` → "Join Month"

### Metadata
JSON format with fields:
- `schema_name` - Name of the schema
- `schema_version` - Version of the schema
- `modification_date` - Date of the modification
- `title` - Title of the schema
- `description` - Description of the schema
- `properties` - Dictionary of properties

#### Properties
- `mix_type` - One of ["Snapshot Date", "Earn Month", "Join Month"]
- `weights` - Dictionary of weight labels and corresponding column names
    - `weight_label` - Label for the weight
    - `weight_column` - Column name for the weight
- `segments` - Dictionary of segment labels and corresponding variable names
    - `segment_label` - Label for the segment
    - `segment_variable` - Variable name for the segment
- `date` - Variable name for the time dimension
- `variable` - Variable name for the characteristic
- `bucket_id` - ID for the bucket
- `bucket_name` - Name of the bucket

## Example Schema/Metadata:
```json
{
        "schema_name": "mix",
        "schema_version": "1",
        "modification_date": "20240331__123456",
        "title": "earn__mix__1__20240331__123456",
        "description": "mix exhibit for earn model version 1",
        "properties": {
            "segments": {
                "Transaction Type": "transactionType"
            },
            "date": "earnMonth",
            "mix_type": "Earn Month",
            "variable": "variable",
            "weights": {
                "Earned Points": "earn"
            },
            "bucket_id": "bucket_id",
            "bucket_name": "bucket_name"
        }
    }
```

## Database Analysis

Based on queries of the sample Earn Month Mix dataset:

### Table Structure
```
column_name    data_type
transactionType STRING
earnMonth      DATE
variable       STRING
bucket_id      DOUBLE
bucket_name    STRING
earn           DOUBLE
table          STRING
schema         STRING
```

### Data Distribution
- **Date Range**: earnMonth spans from 2015-07-01 to 2021-01-01 in monthly increments
- **Transaction Types**: 5 types (Earn 1, Earn 2, Earn 3, Earn 4, Earn 5)
- **Weight Range**: earn values range from ~0.001 to ~9.8 billion, with an average of ~178 million
- **Variable Count**: 12 different characteristics (e.g., Bucket Earn Group, Bucket TSL 2 Group)
- **Bucket Distribution**: Variables have different bucket counts, ranging from 3 buckets (Tier Group) to 36 buckets (Bucket TSL 2 Group)

## Implementation Details

### Core Data Flow
1. User selects a dataset (consolidated name)
2. Application fetches metadata from Redis
3. Weight and date options are populated based on mix type
4. When user selects dates and weight:
   - Segment bubbler is populated with available segments
   - Variable bubbler shows variables ranked by KL divergence
5. User selects a segment (optional) and variable
6. Distribution comparison graph shows the distribution for the selected variable

### Metadata Initialization Process
The application initializes its metadata on startup through the following process:

1. **Database Schema Discovery**
   - Application queries tables in the 'mix' schema
   - Tables are filtered based on naming conventions
   - Tables are grouped by model, version, and creation date

2. **Metadata Extraction**
   - For each data table, the corresponding schema table is identified
   - Schema information is extracted and parsed
   - Mix type is determined from the table name prefix

3. **Redis Storage**
   - Table mappings are stored in Redis under the "table_mappings" key
   - Schema properties are stored under the "lookup_mappings" key
   - These Redis values are used throughout the application for metadata lookup

### Database Access
The application uses a cached approach for database queries to improve performance. Key database access functions include:

1. **get_available_dates(consolidated_name)**
   - Fetches distinct dates from the database for the selected dataset
   - Cached for 2 hours to reduce database load
   - Implementation in `utils/dbx_utils.py`

2. **get_segment_bubbler_data(consolidated_name, weight)**
   - Retrieves segment data with weight calculations
   - Groups data by segment variables defined in metadata
   - Cached to improve performance
   - Implementation in `utils/dbx_utils.py`

3. **get_variable_bubbler_data(consolidated_name, selected_segments, date1, date2, weight)**
   - Calculates KL divergence for variables between two dates
   - Filters by selected segments if provided
   - Ranks variables by KL divergence
   - Cached for performance optimization
   - Implementation in `utils/dbx_utils.py`

4. **update_distribution_comparison(consolidated_name, selected_variable, date1, date2, weight, view_type)**
   - Fetches distribution data for the selected variable and dates
   - Creates either histogram or stacked chart based on view type
   - Implementation in `utils/viz_functions.py`

### KL Divergence Calculation
The KL divergence is calculated using SQL queries directly in the database:

```sql
WITH bucket_data AS (
    SELECT 
        {date_column} as date,
        {variable_column} as variable,
        {bucket_id_column} as bucket_id,
        SUM({weight_column}) AS weight,
        -- Other aggregations
    FROM 
        {table_path}
    WHERE 
        {segment_filters}
    GROUP BY 
        {date_column},
        {variable_column},
        {bucket_id_column}
),
normalized_data AS (
    SELECT
        date,
        variable,
        bucket_id,
        weight,
        weight / SUM(weight) OVER (PARTITION BY date, variable) AS normalized_weight
    FROM bucket_data 
),
kl_divergence AS (  
    SELECT
        variable,
        SUM(
            CASE 
                WHEN date = '{date1}' THEN
                    normalized_weight * LOG(
                        normalized_weight / 
                        NULLIF(
                            MAX(CASE WHEN date = '{date2}' THEN normalized_weight ELSE NULL END) 
                            OVER (PARTITION BY variable, bucket_id),
                            0
                        )
                    )
                ELSE 0 
            END
        ) AS kl_divergence
    FROM normalized_data
    GROUP BY variable
)
SELECT
    variable,
    kl_divergence
FROM kl_divergence
ORDER BY kl_divergence DESC;
```

### Visualization Implementation
Visualizations are created using Plotly with custom color schemes and formatting:

1. **Histogram View**
   - Shows side-by-side bars for date1 and date2
   - Normalized to 100% for direct comparison
   - Implementation in `utils/viz_functions.py:create_histogram_figure()`

2. **Mix View (Stacked Chart)**
   - Shows 100% stacked view for better comparison of distributions
   - Custom color palettes for visual distinction
   - Implementation in `utils/viz_functions.py:create_mix_figure()`

### User Interface
The UI is built with a combination of Dash components and custom styling:

1. **Control Ribbon**
   - Contains date selectors, weight selector, and view toggle
   - Dynamically updates labels based on mix type
   - Implementation in `utils/components.py:create_control_items_card()`

2. **Bubbler Components**
   - Implemented using AG-Grid for interactive data display
   - Supports sorting, filtering, and selection
   - Implementation in `utils/components.py:create_bubbler()` and `utils/bubbler_functions.py`

3. **Distribution Comparison Graph**
   - Uses Plotly for interactive visualization
   - Supports different view modes (histogram/mix)
   - Implementation in `utils/viz_functions.py`

## Error Handling

The application includes comprehensive error handling:

1. **Database Errors**
   - Custom error logging with unique error IDs
   - Graceful fallbacks when data is unavailable
   - Implementation in `utils/exception_handlers.py`

2. **Data Validation**
   - Input validation before database queries
   - Default values when selections are invalid
   - Implementation throughout callback functions

3. **Loading States**
   - Visual indicators during data loading
   - Placeholder states when data is unavailable
   - Implemented in UI components

## Caching Strategy

The application uses Redis for two types of caching:

1. **Metadata Caching**
   - Table mappings and schema properties stored in Redis
   - Used for lookup of table paths and property definitions
   - Implementation in `redis_client.py`

2. **Query Result Caching**
   - Database query results cached using Flask-Caching
   - 2-hour timeout for cached results
   - Implementation with `@cache.memoize` decorators in `utils/dbx_utils.py`

### Redis Data Structure

#### Table Mappings Structure
Redis key: `table_mappings`

```json
{
    "model__mix__version__date__time": {
        "mix_type": "Snapshot Date",  // or "Join Month" or "Earn Month"
        "full_path": "catalog.schema.table_name",
        "consolidated_name": "table_name"
    }
}
```

#### Lookup Mappings Structure
Redis key: `lookup_mappings`

```json
{
    "catalog.schema.table_name": {
        "properties": {
            "mix_type": "Snapshot Date",
            "weights": {
                "Member Count": "member_count",
                "Outstanding Points": "outstanding_points"
            },
            "segments": {
                "Transaction Type": "transactionType"
            },
            "date": "snapshotDate",
            "variable": "characteristic",
            "bucket_id": "bucket_id",
            "bucket_name": "bucket_name"
        }
    }
}
```

## Recent Improvements

1. **Performance Optimizations**
   - Implemented caching for frequently accessed data
   - Optimized SQL queries for faster KL divergence calculation (Yet to apply)
   - Reduced unnecessary callback triggers

2. **UI Enhancements**
   - Improved bubbler components with AG-Grid
   - Added loading indicators for better user feedback
   - Enhanced visualization with custom color schemes

3. **Error Handling**
   - Added comprehensive error logging
   - Improved error messages for user-friendly feedback
   - Implemented fallbacks for missing data

4. **Code Organization**
   - Modular design with separate utility modules
   - Better separation of concerns between data, visualization, and UI
   - Enhanced maintainability with clear function documentation
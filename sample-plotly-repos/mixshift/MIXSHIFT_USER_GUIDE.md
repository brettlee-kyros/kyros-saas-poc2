## MixShift Dashboard Usage Guide
                    
### Overview

The MixShift dashboard helps you quickly identify if mix shifts are driving trends in triangles across three different mix types:
- **Snapshot Date Mix** - How distributions change between two Snapshot Dates
- **Earn Month Mix** - How distributions change between two Earn Months
- **Join Month Mix** - How distributions change between two Join Months

### Getting Started

1. **Dataset Selection**:
    - Choose a dataset using the Dataset Selector
    - The Mix Type will automatically display based on your selection

2. **Date Selection**:
    - Select Date 1 and Date 2 to compare distributions between two time points
    - The date label will change based on mix type (Snapshot Date, Earn Month, or Join Month)

3. **Weight Selection**:
    - Select the appropriate weight measure for your analysis:
        * Snapshot Date Mix: Member counts or outstanding points
        * Earn Month Mix: Primarily earned points
        * Join Month Mix: Primarily member count

4. **Segments and Variables**:
    - Use the Segment Bubbler to filter data to specific segments:
        * Snapshot Date Mix: Clusters or Manual Dimensions
        * Earn Month Mix: Earn Types
        * Join Month Mix: Join Channels
    - Use the Variable Bubbler to select characteristics to analyze (sorted by KL Divergence)

5. **Visualization Options**:
    - Toggle between Histogram View and Mix View (100% stacked chart)
    - Histogram View shows side-by-side comparison of distributions
    - Mix View shows a 100% stacked chart for better temporal comparison

### Understanding KL Divergence

KL Divergence is a statistical measure that quantifies how different two distributions are:
- Higher values indicate greater differences between distributions
- Variables in the Variable Bubbler are ranked by KL Divergence (highest to lowest)
- Use this measure to identify which characteristics show the most significant mix shifts

![KL Divergence](assets\images\KL_Div_Equation.png)
### Analysis Tips

1. **Start broad, then narrow down**:
    - Begin by examining variables with the highest KL Divergence
    - Filter to specific segments to focus your analysis

2. **Compare across different weights**:
    - For Snapshot Date Mix, try both member counts and outstanding points
    - Different weights may reveal different patterns

3. **Use both visualization types**:
    - Histogram View for direct comparison between two dates
    - Mix View for better visualization of distribution differences over time

4. **Interpret results in context**:
    - Consider both the magnitude of KL Divergence and the business significance
    - Look for patterns across related variables
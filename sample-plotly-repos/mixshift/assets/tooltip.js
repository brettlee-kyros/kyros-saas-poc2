window.dccFunctions = window.dccFunctions || {};

// Function to transform slider values into date strings using dynamic data
window.dccFunctions.customDateTransform = function(value) {
    // Ensure schemaDates is defined and is an array with valid length
    if (Array.isArray(window.schemaDates) && window.schemaDates.length > 0) {
        if (value >= 0 && value < window.schemaDates.length) {
            return window.schemaDates[value];  // Return the corresponding date (Month-Year) for the slider value
        } else {
            return '';  // Value out of range
        }
    } else {
        console.error("schemaDates is not properly initialized or is empty.");
        return '';  // Return an empty string if schemaDates is not defined
    }
};

// Function to dynamically update  dates in the global window object
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        updateSchemaDates: function(dates) {
            if (Array.isArray(dates) && dates.length > 0) {
                window.schemaDates = dates;  // Update the global schemaDates
            } else {
                console.error("Invalid date range passed to updateSchemaDates.");
            }
            return null;
        }
    }
});
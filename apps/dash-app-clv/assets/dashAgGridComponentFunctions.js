var dagcomponentfuncs = (window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.BarRenderer = function(props) {
    const value = props.value;
    // Return empty div if value is null
    if (value === null || value === undefined) {
        return React.createElement('div', {});
    }
    
    const maxValue = props.context?.maxValue || 100; // Use global maxValue or default to 100
    const percentage = (value / maxValue) * 50;  // Scale to 50% for one direction
    const isPositive = value >= 0;

    // Format large numbers
    const formatNumber = (num) => {
        if (Math.abs(num) <= 1) {  // Changed to <= to include -1 and 1
            return num.toFixed(4);
            } else if (Math.abs(num) >= 1000000000000) { // Trillion
            return (num / 1000000000000).toFixed(1) + 'T';
        } else if (Math.abs(num) >= 1000000000) { // Billion
            return (num / 1000000000).toFixed(1) + 'B';
        } else if (Math.abs(num) >= 1000000) { // Million
            return (num / 1000000).toFixed(1) + 'M';
        } else if (Math.abs(num) >= 1000) { // Thousand
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toLocaleString();
    };
    
    return React.createElement(
        'div',
        {
            style: {
                display: 'flex',
                alignItems: 'center',
                height: '100%',
                width: '100%',
                position: 'relative',
            }
        },
        [
            // Center line
            React.createElement(
                'div',
                {
                    style: {
                        position: 'absolute',
                        left: '50%',
                        height: '20px',
                        width: '1px',
                        backgroundColor: '#e0e0e0'
                    }
                }
            ),
            // Bar
            React.createElement(
                'div',
                {
                    style: {
                        backgroundColor: '#64B5F6',
                        width: `${Math.abs(percentage)}%`,
                        height: '18px',
                        borderRadius: '1px',
                        position: 'absolute',
                        left: isPositive ? '50%' : `${50 - Math.abs(percentage)}%`,
                        transition: 'width 0.3s ease, left 0.3s ease' // Optional: for smooth transitions
                    }
                }
            ),
            // Value
            React.createElement(
                'span',
                {
                    style: {
                        position: 'absolute',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        fontWeight: '1000',
                        fontSize: '12px',
                        zIndex: 1
                    }
                },
                formatNumber(value)
            )
        ]
    );
};
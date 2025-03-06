let globalHourlyForecasts = []; // To store hourly forecast data for CSV download

document.addEventListener('DOMContentLoaded', function() {
    // Set default date-time value to current date and time
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('timestamp').value = now.toISOString().slice(0, 16);

    // Daily forecast form submission handler
    const dailyForm = document.getElementById('predict-form');
    dailyForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitDailyForecastRequest();
    });

    // Hourly forecast button click handler
    document.getElementById('hourly-forecast-button').addEventListener('click', function(e) {
        submitHourlyForecastRequest();
    });

    // Download CSV button handler
    document.getElementById('download-csv').addEventListener('click', function(e) {
        downloadCSV();
    });
});

function submitDailyForecastRequest() {
    const location = document.getElementById('location').value;
    const timestamp = document.getElementById('timestamp').value;

    document.getElementById('loading').style.display = 'block';
    document.getElementById('daily-results-container').style.display = 'none';
    document.getElementById('hourly-results-container').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';

    const payload = {
        location: location,
        timestamp: new Date(timestamp).toISOString()
    };

    fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(handleResponse)
    .then(data => {
        displayDailyResults(data);
    })
    .catch(error => {
        displayError(error.message);
    })
    .finally(() => {
        document.getElementById('loading').style.display = 'none';
    });
}

function submitHourlyForecastRequest() {
    const location = document.getElementById('location').value;
    const timestamp = document.getElementById('timestamp').value;

    document.getElementById('loading').style.display = 'block';
    document.getElementById('daily-results-container').style.display = 'none';
    document.getElementById('hourly-results-container').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';

    const payload = {
        location: location,
        timestamp: new Date(timestamp).toISOString()
    };

    fetch('/predict_hourly', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(handleResponse)
    .then(data => {
        globalHourlyForecasts = data.forecasts; // Save data for CSV download
        displayHourlyResults(data);
    })
    .catch(error => {
        displayError(error.message);
    })
    .finally(() => {
        document.getElementById('loading').style.display = 'none';
    });
}

function handleResponse(response) {
    if (!response.ok) {
        return response.json().then(data => {
            throw new Error(data.error || 'An error occurred while processing your request.');
        });
    }
    return response.json();
}

function displayDailyResults(data) {
    document.getElementById('daily-prediction-message').textContent = data.message;
    document.getElementById('daily-plot-image').src = "data:image/png;base64," + data.plot_image;
    document.getElementById('daily-results-container').style.display = 'block';
    document.getElementById('daily-results-container').scrollIntoView({ behavior: 'smooth' });
}

function displayHourlyResults(data) {
    const container = document.getElementById('hourly-cards-container');
    container.innerHTML = ''; // Clear previous results

    if (!data.forecasts || data.forecasts.length === 0) {
        container.innerHTML = '<p>No hourly forecast data available.</p>';
    } else {
        data.forecasts.forEach(dayGroup => {
            // Create a header for the day
            const dayHeader = document.createElement('h3');
            dayHeader.textContent = `Forecast for ${dayGroup.date}`;
            container.appendChild(dayHeader);

            // Create a container for the day's cards
            const dayContainer = document.createElement('div');
            dayContainer.className = 'cards-container';

            dayGroup.forecasts.forEach(forecast => {
                const card = document.createElement('div');
                card.className = 'forecast-card';
                card.innerHTML = `
                    <h4>${forecast.timestamp.split(" ")[1]}</h4>
                    <p>Demand: <strong>${forecast.predicted_energy_demand.toFixed(0)} MW</strong></p>
                    <p>Temp: ${forecast.temperature.toFixed(1)}°C</p>
                    <p>Humidity: ${forecast.humidity}%</p>
                `;
                dayContainer.appendChild(card);
            });
            container.appendChild(dayContainer);
        });
    }

    document.getElementById('hourly-results-container').style.display = 'block';
    document.getElementById('hourly-results-container').scrollIntoView({ behavior: 'smooth' });
}

function downloadCSV() {
    if (globalHourlyForecasts.length === 0) {
        alert("No forecast data available to download.");
        return;
    }

    // Flatten the grouped forecast data if needed (globalHourlyForecasts is an array of day groups)
    let csvContent = "data:text/csv;charset=utf-8,Date,Time,Predicted Energy Demand (MW)\n";
    globalHourlyForecasts.forEach(dayGroup => {
        dayGroup.forecasts.forEach(item => {
            // item.timestamp is in "YYYY-MM-DD HH:MM:SS" format
            let [date, time] = item.timestamp.split(" ");
            csvContent += `${date},${time},${item.predicted_energy_demand.toFixed(0)}\n`;
        });
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "hourly_forecast.csv");
    document.body.appendChild(link); // Required for FF

    link.click();
    document.body.removeChild(link);
}

function displayError(errorMessage) {
    const errorElement = document.getElementById('error-message');
    errorElement.textContent = errorMessage;
    errorElement.style.display = 'block';
    errorElement.scrollIntoView({ behavior: 'smooth' });
}

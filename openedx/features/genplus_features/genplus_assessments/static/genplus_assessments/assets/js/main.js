
const ctx = document.getElementById('radarChart');
const myChart = new Chart(ctx, {
    type: 'radar',
    data: {
        labels: ['Collaboration', 'Resilience', 'Initiative', 'Communication', 'Leadership', 'Organisation'],
        datasets: [
        {
            label: 'Start of Year',
            data: [2, 6, 3, 5, 2, 3],
            backgroundColor: 'rgba(99, 217, 255, .24)',
            borderColor: 'rgba(99, 217, 255, 1)',
            pointBackgroundColor: 'rgba(99, 217, 255, 1)',
            pointBorderWidth: 1,
            pointWidth: 6,
            borderWidth: 2,
        },
        {
            label: 'End of Year',
            data: [4, 9, 6, 8, 4, 6],
            backgroundColor: 'rgba(255, 1, 157, .24)',
            borderColor: 'rgba(255, 1, 157, 1)',
            pointBackgroundColor: 'rgba(255, 1, 157, 1)',
            pointBorderWidth: 1,
            pointWidth: 6,
            borderWidth: 2,
        },
        ],
    },
    options: {
        responsive: true,
        scales: {
        r: {
            angleLines: {
            color: '#1c223f',
            },
            grid: {
            color: '#1c223f',
            },
            suggestedMin: 0,
            pointLabels: {
            font: {
                size: 15,
            },
            color: '#1c223f',
            pointBorderColor: '#1c223f',
            },
            ticks: {
            backdropColor: '#1c223f',
            color: '#fff',
            beginAtZero: true,
            fontSize: 20,
            },
        },
        },
        plugins: {
        legend: {
        position: 'bottom',
        labels: {
            usePointStyle: true,
            pointStyle: 'circle',
            boxWidth: 6,
            boxHeight: 6,
            font: {
            size: 12,
            },
            color: '#1c223f',
        },
        },
    },
    },
});


const ctx = document.getElementById('likertChart');
const myChart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: [
      "Communication",
      "Organisation",
      "Resilience"
    ],
    datasets: [
      {
        label: "Not confident",
        data: [ -3, 0, -50 ],
        backgroundColor: "#f26ca7"
      },
      {
        label: "Not confident at all",
        data: [ -7, -100, 0 ],
        backgroundColor: "#ed217c"
      },
      {
        label: "Confident",
        data: [ 0, 0, 0 ],
        backgroundColor: "#8a94f9"
      },
      {
        label: "Very confident",
        data: [ 0, 0, 50 ],
        backgroundColor: "#5863f8"
      }
    ]
  },
  options: {
    barThickness: 25,
    indexAxis: 'y',
    elements: {
      bar: {
        inflateAmount: 0,
      },
    },
    plugins: {
      title: {
        display: false,
      },
      legend: {
        position: 'bottom',
        labels: {
          usePointStyle: true,
          boxWidth: 8,
          boxHeight: 8,
          generateLabels: (chart) => {
            const [notConfident, notConfidentAtAll, ...rest] = chart.data.datasets;
            const sortedData = [notConfidentAtAll, notConfident, ...rest];
            return sortedData.map(({ label, backgroundColor }, index) => {
              let dataIndex = 0;
              if (index === 0) {
                dataIndex = 1;
              } else if (index === 1) {
                dataIndex = 0;
              } else {
                dataIndex = index;
              }
              return {
                text: label,
                fillStyle: backgroundColor,
                strokeStyle: backgroundColor,
                datasetIndex: dataIndex,
                textAlign: 'left',
                hidden: chart ? chart.getDatasetMeta(dataIndex).hidden : false,
              };
            });
          },
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const value = context.formattedValue;
            return `${context?.dataset?.label} ${value < 0 ? value * -1 : value}%`;
          },
        },
      },
    },
    scales: {
      x: {
        stacked: true,
        grid: {
          color: 'transparent',
        },
        ticks: {
          font: {
            size: 13,
            weight: 300,
            family: 'IBM Plex Sans, Readex Pro',
          },
          callback: (value) => `${Math.abs(value)}${value === 0 ? '' : '%'}`,
        },
        min: -100,
        max: 100,
      },
      y: {
        stacked: true,
        grid: {
          color: 'transparent',
        },
        ticks: {
          font: {
            size: 12,
            weight: 300,
            family: 'IBM Plex Sans, Readex Pro',
          },
        },
      },
    },
  },
});

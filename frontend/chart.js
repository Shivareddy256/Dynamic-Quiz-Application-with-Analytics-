// Initialize all charts on the page
document.addEventListener('DOMContentLoaded', function() {
    // Main Quiz Performance Chart
    const quizChartEl = document.getElementById('quizChart');
    if (quizChartEl) {
        const ctx = quizChartEl.getContext('2d');
        const chartData = {
            labels: JSON.parse(quizChartEl.dataset.labels || '[]'),
            datasets: [
                {
                    label: 'Correct Answers',
                    data: JSON.parse(quizChartEl.dataset.correct || '[]'),
                    backgroundColor: 'rgba(75, 192, 192, 0.7)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Incorrect Answers',
                    data: JSON.parse(quizChartEl.dataset.incorrect || '[]'),
                    backgroundColor: 'rgba(255, 99, 132, 0.7)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        };

        new Chart(ctx, {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Responses'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Quiz Title'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Quiz Performance Overview'
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const total = context.dataset.data[context.dataIndex] + 
                                             chartData.datasets[1 - context.datasetIndex].data[context.dataIndex];
                                const percentage = Math.round((context.dataset.data[context.dataIndex] / total) * 100);
                                return `Percentage: ${percentage}%`;
                            }
                        }
                    }
                }
            }
        });
    }
}); 
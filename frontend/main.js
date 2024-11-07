const fileInput = document.getElementById('file');
const heaInput = document.getElementById('hea');
const uploadButton = document.getElementById('upload');
const indexInput = document.getElementById('indexInput');
let currentIndex = 0;
var ecgChart = null;

fetchAll = async () => {
    drawECGChart([]);
    await getDataFromFile();
    showChart();
}

getDataFromFile = async () => {
    uploadButton.addEventListener('click', async (e) => {
        e.preventDefault();
        const file = fileInput.files[0];
        const heaFile = heaInput.files[0];

        if (!file) {
            alert('Please select a .dat file.');
            return;
        }

        if (!heaFile) {
            alert('Please select a .hea file.');
            return;
        }

        const fileName = file.name;
        const fileExtension = fileName.split('.').pop().toLowerCase();
        if (fileExtension !== 'dat') {
            alert('Please upload a file with the .dat extension.');
            return;
        }

        const heaFileName = heaFile.name;
        const heaFileExtension = heaFileName.split('.').pop().toLowerCase();
        if (heaFileExtension !== 'hea') {
            alert('Please upload a file with the .hea extension.');
            return;
        }

        const formData = new FormData();
        formData.append('dat_file', file);
        formData.append('hea_file', heaFile);

        const response = await fetch('http://localhost:8000/upload_file', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            alert('Failed to upload files.');
        } else {
            alert('Files uploaded successfully.');
        }
    });
}

function drawECGChart(ecgData = [], time_range = [], start_time = 0) {
    if (ecgChart) {
        ecgChart.destroy();
    }

    const ctx = document.getElementById('ecgChart').getContext('2d');

    let dataRed = [];
    let dataGreen = [];
    let labels = ecgData.map((_, index) => ((start_time + index) / 360).toFixed(2));  // Convert to time units and format to 2 decimal places

    let timeRangeInTime = time_range.map(range => [range[0] / 360, range[1] / 360]);

    for (let i = 0; i < ecgData.length; i++) {
        let time = (start_time + i) / 360;  // Adjust index to time

        let inRange = false;
        for (let range of timeRangeInTime) {
            if (time >= range[0] && time <= range[1]) {
                inRange = true;
                break;
            }
        }

        if (inRange) {
            dataRed.push(ecgData[i]);
            dataGreen.push(null);
        } else {
            dataGreen.push(ecgData[i]);
            dataRed.push(null);
        }
    }

    ecgChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Abnormal',
                    data: dataRed,
                    borderColor: 'red',
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0
                },
                {
                    label: 'Normal',
                    data: dataGreen,
                    borderColor: 'green',
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0
                }
            ]
        },
        options: {
            scales: {
                x: { title: { display: true, text: 'Time (s)' } },
                y: { title: { display: true, text: 'Amplitude' } }
            }
        }
    });
}

async function getEcgData(index) {
    const ecgDatatmp = await fetch(`http://localhost:8000/get_segments?index=${index}`);
    const ecgDataJson = await ecgDatatmp.json();
    let ecgDataList = ecgDataJson['segment_signal'];
    let label = ecgDataJson['label'];
    let time_range = ecgDataJson['time_range'];
    let start_time = ecgDataJson['start_time'];  // Assume the response includes 'start_time'
    return [ecgDataList, label, time_range, start_time];
}

async function getAllEcgData(startIndex = 0) {
    let ecgData = [];
    let time_range = [];
    let start_time = 0;

    for (let i = startIndex; i < startIndex + 10; i++) {
        let data = await getEcgData(i);
        ecgData = ecgData.concat(data[0]);
        if (i === startIndex) {
            start_time = data[3];  // Set start time only once from the first segment
        }
        if (data[1] === "A") {
            time_range.push(data[2]);
        }
    }
    return [ecgData, time_range, start_time];
}

async function showChart(startIndex = 0) {
    let allEcgData = await getAllEcgData(startIndex);
    let ecgData = allEcgData[0];
    let time_range = allEcgData[1];
    let start_time = allEcgData[2];
    console.log(`Showing data from index ${startIndex} to ${startIndex + 9}`);
    drawECGChart(ecgData, time_range, start_time);
}

document.getElementById('next').addEventListener('click', async (e) => {
    e.preventDefault();
    currentIndex += 10;
    await showChart(currentIndex);
});

document.getElementById('back').addEventListener('click', async (e) => {
    e.preventDefault();
    if (currentIndex > 0) {
        currentIndex -= 10;
        await showChart(currentIndex);
    }
});

document.getElementById('indexInput').addEventListener('change', async (e) => {
    currentIndex = parseInt(e.target.value, 10);
    if (isNaN(currentIndex) || currentIndex < 0) {
        alert('Please enter a valid index.');
        return;
    }
    await showChart(currentIndex);
});

fetchAll();

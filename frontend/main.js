const fileInput = document.getElementById('file');
const uploadButton = document.getElementById('upload');

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
        if (!file) {
            alert('Please select a file first.');
            return;
        }
    // Check if file extension is .dat
        const fileName = file.name;
        const fileExtension = fileName.split('.').pop().toLowerCase();
        if (fileExtension !== 'dat') {
          alert('Please upload a file with the .dat extension.');
          return;
        }
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('http://localhost:8000/upload_file', {
          method: 'POST',
          body: formData
        });
    })
}

// Chia dữ liệu thành hai nửa
function drawECGChart(ecgData = [], time_range = []){
    if (ecgChart) {
        ecgChart.destroy();
    }

    const ctx = document.getElementById('ecgChart').getContext('2d');

    let dataRed = [];
    let dataGreen = [];
    let labels = ecgData.map((_, index) => index);

    // Duyệt qua từng phần tử trong dữ liệu ECG
    for (let i = 0; i < ecgData.length; i++) {
        let inRange = false;
        // Kiểm tra xem vị trí i có thuộc vào một trong các khoảng không
        for (let range of time_range) {
            if (i >= range[0] && i <= range[1]) {
                inRange = true;
                break;
            }
        }

        if (inRange) {
            dataRed.push(ecgData[i]);
            dataGreen.push(null); // Không vẽ dữ liệu xanh cho đoạn đỏ
        } else {
            dataGreen.push(ecgData[i]);
            dataRed.push(null); // Không vẽ dữ liệu đỏ cho đoạn xanh
        }
    }

    // Vẽ biểu đồ
    ecgChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,  // Nhãn x-axis
            datasets: [
                {
                    label: 'ECG Data (Red)',
                    data: dataRed,
                    borderColor: 'red',  // Màu đỏ cho dữ liệu đỏ
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0 // Ẩn các điểm trên đồ thị
                },
                {
                    label: 'ECG Data (Green)',
                    data: dataGreen,
                    borderColor: 'green',  // Màu xanh lá cho dữ liệu xanh
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0 // Ẩn các điểm trên đồ thị
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
async function getEcgData(index){
    const ecgDatatmp = await fetch(`http://localhost:8000/get_segments?index=${index}`);
    const ecgDataJson = await ecgDatatmp.json();
    let ecgDataList = ecgDataJson['segment_signal'];
    let label = ecgDataJson['label'];
    let time_range = ecgDataJson['time_range'];
    return [ecgDataList, label, time_range];
}

async function getAllEcgData () {
    let ecgData = [];
    let time_range = [];
    for (let i = 0; i < 10; i++) {
        data = await getEcgData(i);
        ecgData = ecgData.concat(data[0]);
        if (data[1] === "A"){
            time_range.push(data[2]);
        }
    }
    return [ecgData, time_range];
}

async function showChart(){
    const showBtn = document.getElementById('show');
    showBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        let allEcgData = await getAllEcgData();
        let ecgData = allEcgData[0];
        let time_range = allEcgData[1];
        console.log(time_range);
        drawECGChart(ecgData, time_range);
    });
}

fetchAll();
const dropArea = document.getElementById('drop-area');
const fileInput = document.getElementById('fileElem');
const gallery = document.getElementById('gallery');
const reportBtn = document.getElementById('reportBtn');
const reportSection = document.getElementById('reportSection');

// drag/drop handlers
dropArea.addEventListener('click', () => fileInput.click());
dropArea.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropArea.classList.add('bg-gray-100');
});
dropArea.addEventListener('dragleave', () => dropArea.classList.remove('bg-gray-100'));
dropArea.addEventListener('drop', (e) => {
  e.preventDefault();
  dropArea.classList.remove('bg-gray-100');
  handleFiles(e.dataTransfer.files);
});
fileInput.addEventListener('change', () => handleFiles(fileInput.files));

function handleFiles(files) {
  gallery.innerHTML = "";
  [...files].forEach(file => {
    let img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    img.className = "mx-auto max-h-80 rounded-2xl shadow-xl";
    gallery.appendChild(img);
  });
  reportBtn.classList.remove("hidden");
}

// show report section
reportBtn.addEventListener("click", () => {
  reportSection.classList.remove("hidden");
  
  // 👉 Здесь можно задать проценты для баров:
  // setProgress("quality", 70);
  // setProgress("sharpness", 55);
  // setProgress("light", 80);
  // setProgress("details", 65);
});

// функция для обновления прогресс-бара
function setProgress(id, value) {
  const bar = document.getElementById(id);
  const label = document.getElementById(`${id}-label`);
  bar.style.width = value + "%";
  label.textContent = value + "%";
}

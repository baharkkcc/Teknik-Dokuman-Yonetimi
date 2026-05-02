// State
let documents = [
    {
        id: 1,
        docNo: "DOC-2024-001",
        docName: "Tesis Güvenlik Prosedürü",
        type: "Prosedür",
        revision: 2,
        date: "02 Mayıs 2026",
        uploader: "Ahmet Yılmaz",
        approver: "-",
        file: "guvenlik_proseduru_v2.pdf",
        status: "Beklemede",
        feedback: ""
    },
    {
        id: 2,
        docNo: "DOC-2024-001",
        docName: "Tesis Güvenlik Prosedürü",
        type: "Prosedür",
        revision: 1,
        date: "28 Nisan 2026",
        uploader: "Ahmet Yılmaz",
        approver: "Ayşe Demir",
        file: "guvenlik_proseduru_v1.pdf",
        status: "Reddedildi",
        feedback: "İmza eksikliği tespit edildi."
    },
    {
        id: 3,
        docNo: "TAL-2024-045",
        docName: "Pres Makinesi Kullanım Talimatı",
        type: "Talimat",
        revision: 1,
        date: "15 Nisan 2026",
        uploader: "Mehmet Kaya",
        approver: "Ayşe Demir",
        file: "makine_kullanim_talimati.pdf",
        status: "Onaylandı",
        feedback: "Uygundur."
    }
];

let selectedDocIdForReject = null;

// DOM Elements
const docTableBody = document.getElementById('docTableBody');
const uploadForm = document.getElementById('uploadForm');
const docFile = document.getElementById('docFile');
const fileNameDisplay = document.getElementById('fileName');
const rejectModal = document.getElementById('rejectModal');
const cancelRejectBtn = document.getElementById('cancelReject');
const confirmRejectBtn = document.getElementById('confirmReject');
const feedbackText = document.getElementById('feedbackText');
const filterType = document.getElementById('filterType');
const filterStatus = document.getElementById('filterStatus');
const filterSearch = document.getElementById('filterSearch');

// Initialization
function init() {
    renderTable();
    setupEventListeners();
}

// Render Table
function renderTable() {
    const typeFilter = filterType ? filterType.value : 'Tümü';
    const statusFilter = filterStatus ? filterStatus.value : 'Tümü';
    const searchFilter = filterSearch ? filterSearch.value.toLowerCase() : '';

    let filteredDocs = documents.filter(doc => {
        const matchType = typeFilter === 'Tümü' || doc.type === typeFilter;
        const matchStatus = statusFilter === 'Tümü' || doc.status === statusFilter;
        const matchSearch = doc.docNo.toLowerCase().includes(searchFilter) || doc.docName.toLowerCase().includes(searchFilter);
        return matchType && matchStatus && matchSearch;
    });

    // Sort globally by revision descending
    const sortedDocs = filteredDocs.sort((a, b) => b.revision - a.revision);
    
    docTableBody.innerHTML = '';
    
    sortedDocs.forEach(doc => {
        const tr = document.createElement('tr');
        
        let statusClass = '';
        if(doc.status === 'Beklemede') statusClass = 'status-beklemede';
        else if(doc.status === 'Onaylandı') statusClass = 'status-onaylandi';
        else if(doc.status === 'Reddedildi') statusClass = 'status-reddedildi';
        else if(doc.status === 'Arşivlendi') statusClass = 'status-arsivlendi';

        tr.className = 'row-clickable';
        tr.onclick = (e) => {
            if(e.target.closest('button') || e.target.closest('a')) return;
            showPreview(doc.id);
        };
        
        tr.innerHTML = `
            <td><strong>${doc.docNo}</strong></td>
            <td>${doc.docName}</td>
            <td>${doc.type}</td>
            <td>${doc.date}</td>
            <td><a href="${doc.fileData || '#'}" ${doc.fileData ? `download="${doc.file}"` : ''} target="_blank" style="color: var(--primary-color); text-decoration: none;">📄 ${doc.file}</a></td>
            <td><span class="status-badge ${statusClass}">${doc.status}</span></td>
            <td style="color: var(--text-secondary); max-width: 200px; font-size: 0.85rem;">${doc.feedback || '-'}</td>
            <td>
                ${doc.status === 'Beklemede' ? `
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-success" onclick="approveDoc(${doc.id})">Onay</button>
                        <button class="btn btn-sm btn-danger" onclick="openRejectModal(${doc.id})">Red</button>
                    </div>
                ` : `<span style="font-size: 0.85rem; color: var(--text-secondary)">İşlem Tamamlandı</span>`}
            </td>
        `;
        
        docTableBody.appendChild(tr);
    });
}

// Event Listeners
function setupEventListeners() {
    if(filterType) filterType.addEventListener('change', renderTable);
    if(filterStatus) filterStatus.addEventListener('change', renderTable);
    if(filterSearch) filterSearch.addEventListener('input', renderTable);

    docFile.addEventListener('change', (e) => {
        if(e.target.files.length > 0) {
            fileNameDisplay.textContent = e.target.files[0].name;
            fileNameDisplay.style.color = "var(--primary-color)";
        } else {
            fileNameDisplay.textContent = "PDF Seçin veya Sürükleyin";
            fileNameDisplay.style.color = "inherit";
        }
    });

    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const docNo = document.getElementById('docNo').value;
        const docName = document.getElementById('docName').value;
        const type = document.getElementById('docType').value;
        
        if(!docFile.files[0]) {
            alert("Lütfen bir PDF dosyası seçin.");
            return;
        }

        const pendingRevision = documents.find(d => d.docNo === docNo && d.status === 'Beklemede');
        if (pendingRevision) {
            alert(`Hata: ${docNo} numaralı dokümanın şu anda incelemede olan bir revizyonu var. Aynı anda birden fazla revizyon onaya sunulamaz.`);
            return;
        }

        const selectedFile = docFile.files[0];
        const fileName = selectedFile.name;

        const reader = new FileReader();
        reader.onload = function(event) {
            const fileDataUrl = event.target.result;

            // Check if docNo exists to determine revision
            const existingDocs = documents.filter(d => d.docNo === docNo);
            let newRevision = 1;
            if(existingDocs.length > 0) {
                const maxRev = Math.max(...existingDocs.map(d => d.revision));
                newRevision = maxRev + 1;
            }
            
            const formattedDate = new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' });

            const newDoc = {
                id: Date.now(),
                docNo,
                docName,
                type,
                revision: newRevision,
                date: formattedDate,
                uploader: "Mevcut Kullanıcı",
                approver: "-",
                file: fileName,
                fileData: fileDataUrl,
                status: "Beklemede",
                feedback: ""
            };

            documents.push(newDoc);
            
            // Reset form
            uploadForm.reset();
            fileNameDisplay.textContent = "PDF Seçin veya Sürükleyin";
            fileNameDisplay.style.color = "inherit";
            
            renderTable();
            
            // Simulate notification
            alert('Doküman başarıyla yüklendi!');
        };
        
        reader.readAsDataURL(selectedFile);
    });

    cancelRejectBtn.addEventListener('click', closeRejectModal);
    
    confirmRejectBtn.addEventListener('click', () => {
        const feedback = feedbackText.value.trim();
        if(!feedback) {
            alert('Lütfen bir ret nedeni girin.');
            return;
        }
        
        rejectDoc(selectedDocIdForReject, feedback);
        closeRejectModal();
    });
    
    // Close modal on click outside
    rejectModal.addEventListener('click', (e) => {
        if(e.target === rejectModal) {
            closeRejectModal();
        }
    });
}

// Actions
window.approveDoc = function(id) {
    const doc = documents.find(d => d.id === id);
    if(doc) {
        documents.forEach(d => {
            if (d.docNo === doc.docNo && d.id !== doc.id && d.status === 'Onaylandı') {
                d.status = 'Arşivlendi';
            }
        });
        
        doc.status = "Onaylandı";
        doc.feedback = "Onaylandı";
        doc.approver = "Yönetici";
        renderTable();
        if(document.getElementById('detailView').style.display === 'block') showPreview(id);
    }
};

window.openRejectModal = function(id) {
    selectedDocIdForReject = id;
    feedbackText.value = '';
    rejectModal.classList.add('active');
};

function closeRejectModal() {
    rejectModal.classList.remove('active');
    selectedDocIdForReject = null;
}

function rejectDoc(id, feedback) {
    const doc = documents.find(d => d.id === id);
    if(doc) {
        doc.status = "Reddedildi";
        doc.feedback = feedback;
        doc.approver = "Yönetici";
        renderTable();
        if(document.getElementById('detailView').style.display === 'block') showPreview(id);
    }
}

function showPreview(id) {
    const doc = documents.find(d => d.id === id);
    if(!doc) return;

    document.getElementById('dashboardView').style.display = 'none';
    document.getElementById('detailView').style.display = 'block';
    
    // Scroll to top
    window.scrollTo(0, 0);

    const previewDetails = document.getElementById('previewDetails');
    const previewIframe = document.getElementById('previewIframe');

    let statusClass = '';
    if(doc.status === 'Beklemede') statusClass = 'status-beklemede';
    else if(doc.status === 'Onaylandı') statusClass = 'status-onaylandi';
    else if(doc.status === 'Reddedildi') statusClass = 'status-reddedildi';
    else if(doc.status === 'Arşivlendi') statusClass = 'status-arsivlendi';

    previewDetails.innerHTML = `
        <div><strong style="color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Döküman No</strong> <span style="color: var(--text-primary); font-size: 1.1rem;">${doc.docNo}</span></div>
        <div><strong style="color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Doküman Adı</strong> <span style="color: var(--text-primary); font-size: 1.1rem;">${doc.docName}</span></div>
        <div><strong style="color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Tarih</strong> <span style="color: var(--text-primary);">${doc.date}</span></div>
        <div><strong style="color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Yükleyen</strong> <span style="color: var(--text-primary);">${doc.uploader}</span></div>
        <div><strong style="color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Onaylayan</strong> <span style="color: var(--text-primary);">${doc.approver}</span></div>
        <div><strong style="color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Durum</strong> <span class="status-badge ${statusClass}">${doc.status}</span></div>
        ${doc.feedback ? `<div style="grid-column: 1 / -1; background: rgba(239, 68, 68, 0.1); padding: 1rem; border-left: 4px solid #ef4444; border-radius: 6px; margin-top: 0.5rem;"><strong style="color:#ef4444; display:block; margin-bottom:0.25rem;">Geri Bildirim</strong>${doc.feedback}</div>` : ''}
    `;

    if(doc.fileData) {
        previewIframe.src = doc.fileData;
        previewIframe.style.display = 'block';
    } else {
        previewIframe.style.display = 'none';
        if(!previewDetails.innerHTML.includes('demo dosyasının')) {
            previewDetails.innerHTML += `<div style="grid-column: 1 / -1; margin-top: 1rem; color: var(--warning-color); padding: 1rem; background: rgba(245, 158, 11, 0.1); border-radius: 8px;">Bu demo dosyasının önizlemesi yok. Yeni PDF yükleyerek deneyin.</div>`;
        }
    }
}

window.closeDetailView = function() {
    document.getElementById('detailView').style.display = 'none';
    document.getElementById('dashboardView').style.display = 'block';
};

// Start
document.addEventListener('DOMContentLoaded', init);

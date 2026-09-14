// Only 2 brand medicines for this demo, each with its own generic alternatives.
const medicineDB = {
    "Biogesic": {
        generic_name: "Paracetamol 500mg",
        rx_required: false,
        generics: [
            { name: "RiteMed Paracetamol", manufacturer: "RiteMed", price: 2.50 },
            { name: "TGP Paracetamol", manufacturer: "The Generics Pharmacy", price: 2.75 }
        ]
    },
    "Coumadin": {
        generic_name: "Warfarin 5mg",
        rx_required: true,
        nti_warning: true,
        generics: [
            { name: "RiteMed Warfarin", manufacturer: "RiteMed", price: 12.00 },
            { name: "Zydus Warfarin", manufacturer: "Zydus Pharma", price: 13.50 }
        ]
    }
};

function showTab(which) {
    document.getElementById('searchTab').classList.toggle('active', which === 'search');
    document.getElementById('scanTab').classList.toggle('active', which === 'scan');
    document.getElementById('searchPanel').classList.toggle('hidden', which !== 'search');
    document.getElementById('resultsLabel').classList.toggle('hidden', which !== 'search');
    document.getElementById('resultsArea').classList.toggle('hidden', which !== 'search');
    document.getElementById('scanPanel').classList.toggle('hidden', which !== 'scan');
    if (which !== 'search') {
        document.getElementById('detailArea').classList.add('hidden');
    }
}

// STEP 1: user types a name -> show matching brand medicine(s)
function handleSearch() {
    const query = document.getElementById('medicineSearch').value.trim().toLowerCase();
    const resultsArea = document.getElementById('resultsArea');
    const resultsLabel = document.getElementById('resultsLabel');
    document.getElementById('detailArea').classList.add('hidden');
    resultsArea.classList.remove('hidden');

    if (query === '') {
        resultsLabel.textContent = 'TYPE A MEDICINE NAME ABOVE';
        resultsArea.innerHTML = '<div class="empty-state">Try "Biogesic" or "Coumadin"</div>';
        return;
    }

    const matches = Object.keys(medicineDB).filter(name => name.toLowerCase().includes(query));

    if (matches.length === 0) {
        resultsLabel.textContent = 'NO MATCHES FOUND';
        resultsArea.innerHTML = '<div class="empty-state">No medicine found for "' + query + '"</div>';
        return;
    }

    resultsLabel.textContent = 'SELECT YOUR MEDICINE';
    let html = '<div class="result-list">';
    matches.forEach(name => {
        const med = medicineDB[name];
        const iconClass = med.nti_warning ? 'warn' : (!med.rx_required ? 'otc' : '');
        const badge = med.rx_required
            ? '<span class="badge-small rx">Rx</span>'
            : '<span class="badge-small otc">OTC</span>';
        html += `
            <div class="result-card" onclick="showGenerics('${name}')">
                <div class="pill-icon ${iconClass}"></div>
                <div class="med-info">
                    <span class="brand-name">${name}</span>
                    <p class="generic-name">${med.generic_name}</p>
                </div>
                ${badge}
                <span class="chevron">›</span>
            </div>`;
    });
    html += '</div>';
    resultsArea.innerHTML = html;
}

// STEP 2: user clicks a medicine -> show its generic alternatives
function showGenerics(name) {
    const med = medicineDB[name];
    document.getElementById('resultsArea').classList.add('hidden');
    document.getElementById('resultsLabel').classList.add('hidden');
    document.getElementById('detailArea').classList.remove('hidden');
    document.getElementById('detailTitle').textContent = name;
    document.getElementById('detailSub').textContent = med.generic_name;

    let html = '';
    med.generics.forEach(g => {
        html += `
            <div class="generic-card">
                <div class="pill-icon"></div>
                <div class="med-info">
                    <span class="brand-name">${g.name}</span>
                    <p class="generic-name">${g.manufacturer}</p>
                    <p class="price">₱${g.price.toFixed(2)}</p>
                </div>
            </div>`;
    });
    if (med.nti_warning) {
        html += '<p class="nti-note" style="padding:10px 4px 0 4px;">⚠ Narrow Therapeutic Index drug — consult your pharmacist or doctor before switching brands.</p>';
    }
    document.getElementById('genericList').innerHTML = html;
}

function backToResults() {
    document.getElementById('detailArea').classList.add('hidden');
    document.getElementById('resultsArea').classList.remove('hidden');
    document.getElementById('resultsLabel').classList.remove('hidden');
}

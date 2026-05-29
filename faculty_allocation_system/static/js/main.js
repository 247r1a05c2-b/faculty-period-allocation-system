// main.js - Client-side JavaScript for Faculty Allocation System
// ---------------------------------------------------------------

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // 1. SIDEBAR TOGGLE
    // ============================================================
    var toggleBtn = document.getElementById('sidebarToggle');
    var sidebar   = document.getElementById('sidebar');
    var main      = document.getElementById('mainContent');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function () {
            sidebar.classList.toggle('hidden');
            sidebar.classList.toggle('open');
            if (main) {
                main.style.marginLeft = sidebar.classList.contains('hidden') ? '0' : '';
            }
        });
    }

    // ============================================================
    // 2. AUTO-DISMISS FLASH ALERTS after 4 seconds
    // ============================================================
    setTimeout(function () {
        document.querySelectorAll('.alert.alert-success, .alert.alert-info').forEach(function (el) {
            var bsAlert = bootstrap.Alert.getOrCreateInstance(el);
            if (bsAlert) bsAlert.close();
        });
    }, 4000);

    // ============================================================
    // 3. LOADING OVERLAY for long-running operations
    //    (allocation & timetable generation)
    // ============================================================
    var loadingForms = document.querySelectorAll(
        'form[action*="run_allocation"], form[action*="generate_timetable"]'
    );

    loadingForms.forEach(function (form) {
        form.addEventListener('submit', function () {
            showLoading(
                form.action.includes('generate') ?
                'Generating timetable with OR-Tools...' :
                'Running AI allocation algorithm...'
            );
        });
    });

    // ============================================================
    // 4. CONFIRM DANGEROUS ACTIONS
    // ============================================================
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (!confirm(el.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });

    // ============================================================
    // 5. HIGHLIGHT ACTIVE NAV LINK (redundant safety for Jinja)
    // ============================================================
    var currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(function (link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // ============================================================
    // 6. TIMETABLE SEARCH (live filter for grid cells)
    //    Used on the admin timetable page
    // ============================================================
    var searchBox = document.getElementById('ttSearch');
    if (searchBox) {
        searchBox.addEventListener('input', function () {
            var val = this.value.toLowerCase().trim();
            document.querySelectorAll('.tt-filled').forEach(function (cell) {
                if (!val) {
                    cell.style.opacity = '1';
                } else {
                    cell.style.opacity = cell.textContent.toLowerCase().includes(val) ? '1' : '0.15';
                }
            });
        });
    }

    // ============================================================
    // 7. PRINT TIMETABLE
    // ============================================================
    var printBtn = document.getElementById('printTimetable');
    if (printBtn) {
        printBtn.addEventListener('click', function () {
            window.print();
        });
    }

    // ============================================================
    // 8. PREFERENCE FORM — prevent duplicate subject selection
    // ============================================================
    var prefSelects = document.querySelectorAll('.pref-select');
    if (prefSelects.length) {
        prefSelects.forEach(function (sel) {
            sel.addEventListener('change', function () {
                var chosen = [];
                prefSelects.forEach(function (s) { if (s.value) chosen.push(s.value); });

                prefSelects.forEach(function (s) {
                    Array.from(s.options).forEach(function (opt) {
                        if (opt.value && chosen.includes(opt.value) && opt.value !== s.value) {
                            opt.disabled = true;
                        } else {
                            opt.disabled = false;
                        }
                    });
                });
            });
        });
    }

});

// ============================================================
// Helper: Show loading overlay with message
// ============================================================
function showLoading(msg) {
    var overlay = document.getElementById('loadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.innerHTML = `
            <div class="spinner-border text-light" style="width:3rem;height:3rem;" role="status"></div>
            <div id="loadingMsg" class="fs-5 fw-semibold">${msg || 'Processing...'}</div>
            <small class="text-light opacity-75">Please wait, this may take a few seconds.</small>`;
        document.body.appendChild(overlay);
    } else {
        var msgEl = overlay.querySelector('#loadingMsg');
        if (msgEl) msgEl.textContent = msg || 'Processing...';
    }
    overlay.classList.add('active');
}

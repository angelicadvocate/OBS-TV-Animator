// Smart Diagnostic System
document.addEventListener('DOMContentLoaded', function() {
    const checkboxes = document.querySelectorAll('.diagnostic-checkbox');
    const resultsDiv = document.getElementById('diagnostic-results');
    const allGoodDiv = document.getElementById('all-good');
    const hasIssuesDiv = document.getElementById('has-issues');
    const troubleshootingSections = document.querySelectorAll('.troubleshooting-section');
    
    // Initially hide all troubleshooting sections
    troubleshootingSections.forEach(section => {
        section.style.display = 'none';
    });
    
    function updateDiagnosticResults() {
        const checkedBoxes = document.querySelectorAll('.diagnostic-checkbox:checked');
        const uncheckedBoxes = document.querySelectorAll('.diagnostic-checkbox:not(:checked)');
        const totalCount = checkboxes.length;
        const checkedCount = checkedBoxes.length;
        
        // Only show results if at least one checkbox is checked
        if (checkedCount === 0) {
            resultsDiv.style.display = 'none';
            // Hide all sections when no checkboxes are selected
            troubleshootingSections.forEach(section => {
                section.style.display = 'none';
            });
            return;
        }
        
        resultsDiv.style.display = 'block';
        
        // Hide all sections first
        troubleshootingSections.forEach(section => {
            section.style.display = 'none';
        });
        
        if (checkedCount === totalCount) {
            // All systems working - show success message and hide all troubleshooting
            allGoodDiv.style.display = 'block';
            hasIssuesDiv.style.display = 'none';
            
            // Update success message to be more helpful
            allGoodDiv.innerHTML = `
                <i class="fa-solid fa-check-circle"></i>
                <strong>All basic systems are working!</strong> 
                If you're still experiencing issues, they might be related to advanced integration or performance. 
                <button onclick="showAllSections()" class="btn-secondary" style="margin-left: 10px; padding: 5px 10px; border-radius: 4px;">
                    Show All Troubleshooting Sections
                </button>
            `;
        } else {
            // Issues detected - show relevant sections
            allGoodDiv.style.display = 'none';
            hasIssuesDiv.style.display = 'block';
            
            // Collect all issue types from unchecked boxes
            const relevantIssueTypes = new Set();
            
            uncheckedBoxes.forEach(checkbox => {
                const relatesTo = checkbox.getAttribute('data-relates-to');
                if (relatesTo) {
                    relatesTo.split(',').forEach(type => {
                        relevantIssueTypes.add(type.trim());
                    });
                }
            });
            
            // Show sections that match the issue types
            let sectionsShown = 0;
            troubleshootingSections.forEach(section => {
                const sectionTypes = section.getAttribute('data-issue-type');
                if (sectionTypes) {
                    const types = sectionTypes.split(',').map(t => t.trim());
                    const hasRelevantType = types.some(type => relevantIssueTypes.has(type));
                    
                    if (hasRelevantType) {
                        section.style.display = 'block';
                        sectionsShown++;
                    }
                }
            });
            
            // Update the issues message with more context
            const issueTypesList = Array.from(relevantIssueTypes).join(', ');
            hasIssuesDiv.innerHTML = `
                <i class="fa-solid fa-exclamation-triangle"></i>
                <strong>Issues detected with:</strong> ${issueTypesList}<br>
                <small>Showing ${sectionsShown} relevant troubleshooting section(s) below. Check off working items above to hide resolved sections.</small>
            `;
        }
    }
    
    // Global function to show all sections (for advanced troubleshooting)
    window.showAllSections = function() {
        troubleshootingSections.forEach(section => {
            section.style.display = 'block';
        });
        
        hasIssuesDiv.style.display = 'block';
        allGoodDiv.style.display = 'none';
        hasIssuesDiv.innerHTML = `
            <i class="fa-solid fa-tools"></i>
            <strong>Advanced Troubleshooting Mode</strong><br>
            <small>Showing all troubleshooting sections for comprehensive debugging.</small>
        `;
    };
    
    // Advanced diagnostics toggle
    const toggleAdvancedBtn = document.getElementById('toggleAdvanced');
    const resetBtn = document.getElementById('resetDiagnostic');
    const advancedDiagnostics = document.querySelectorAll('.advanced-diagnostic');
    let advancedVisible = false;
    
    toggleAdvancedBtn.addEventListener('click', function() {
        advancedVisible = !advancedVisible;
        
        advancedDiagnostics.forEach(item => {
            item.style.display = advancedVisible ? 'block' : 'none';
        });
        
        this.innerHTML = advancedVisible 
            ? '<i class="fa-solid fa-minus"></i> Hide Advanced Diagnostics'
            : '<i class="fa-solid fa-plus"></i> Show Advanced Diagnostics';
        
        // Re-run diagnostic check with new checkboxes
        updateDiagnosticResults();
    });
    
    // Reset functionality
    resetBtn.addEventListener('click', function() {
        document.querySelectorAll('.diagnostic-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Hide advanced diagnostics
        advancedVisible = false;
        advancedDiagnostics.forEach(item => {
            item.style.display = 'none';
        });
        toggleAdvancedBtn.innerHTML = '<i class="fa-solid fa-plus"></i> Show Advanced Diagnostics';
        
        // Reset results
        resultsDiv.style.display = 'none';
        troubleshootingSections.forEach(section => {
            section.style.display = 'none';
        });
    });
    
    // Add event listeners to all checkboxes (including advanced ones)
    function addCheckboxListeners() {
        document.querySelectorAll('.diagnostic-checkbox').forEach(checkbox => {
            checkbox.removeEventListener('change', updateDiagnosticResults); // Remove existing
            checkbox.addEventListener('change', updateDiagnosticResults); // Add fresh listener
        });
    }
    
    addCheckboxListeners();
    
    // Run initial check in case any boxes are pre-checked
    updateDiagnosticResults();
});
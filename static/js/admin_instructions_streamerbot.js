function copyToClipboard(textOrElementId) {
    let text;
    let button;
    
    // Check if it's an element ID or direct text
    if (textOrElementId.startsWith('http://')) {
        // Direct URL text
        text = textOrElementId;
        button = event.target;
    } else {
        // Element ID (existing functionality)
        const element = document.getElementById(textOrElementId);
        text = element.textContent;
        button = element.parentElement.querySelector('.copy-button');
    }
    
    navigator.clipboard.writeText(text).then(function() {
        // Show success feedback
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
        setTimeout(() => {
            button.innerHTML = originalText;
        }, 2000);
    }).catch(function(err) {
        console.error('Failed to copy text: ', err);
        button.innerHTML = '<i class="fa-solid fa-times"></i> Failed';
        setTimeout(() => {
            button.innerHTML = originalText;
        }, 2000);
    });
}
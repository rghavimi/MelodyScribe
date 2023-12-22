document.getElementById('file').addEventListener('change', function() {
    var fileName = this.files[0].name; // Gets the file name
    document.getElementById('file-chosen').textContent = fileName; // Updates the text
});

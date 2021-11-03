var socketResume = io.connect('http://' + document.domain + ':' + location.port + '/resume');

var calendar;

document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
  
    resume = new Resume(calendarEl, socketResume);

    resume.render();

});
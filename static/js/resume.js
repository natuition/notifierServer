class Resume {
    constructor(element, socketio) {
        if(element instanceof HTMLDivElement) this.element = element;
        else{
            console.log("Passed element must be a div !");
            this.element = None;
        }
        this.socketio = socketio;
        this.CHART_COLORS = {
            red: 'rgba(255, 99, 132, 1)',
            orange: 'rgba(255, 159, 64, 1)',
            yellow: 'rgba(255, 205, 86, 1)',
            green: 'rgba(75, 192, 192, 1)',
            blue: 'rgba(54, 162, 235, 1)',
            purple: 'rgba(153, 102, 255, 1)',
            grey: 'rgba(201, 203, 207, 1)'
        };
        this.week = new Array('Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche');
        this.months = new Array('Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre');
        this.unitTime = "heure";
        this.renderDay = new Date();
        this.loadChartMonday = this.mondaysInMonth(this.renderDay.getMonth()+1,this.renderDay.getFullYear())[0];
        this.loadChartSn = null;
        this.reloaderData = null;
        this.dataRecv = null;
        this.socketio.on('sendData', (d)=>{
            if(JSON.stringify(this.dataRecv) !== JSON.stringify(d)){
                this.dataRecv = d;
                this.rendering();
            }
        });
    }

    buttonCreator(label, id, isSmall, style=""){
        var button = document.createElement('button');
        button.appendChild(document.createTextNode(label));
        button.setAttribute('id', id);
        button.setAttribute('type', 'button');
        button.setAttribute('class', (isSmall) ? 'btn btn-light btn-sm' : 'btn btn-light');
        button.setAttribute('style',"background-color: #e9ecef; color: #495057; cursor: pointer;"+style);
        button.setAttribute('onmouseover',"this.style.background='#495057'; this.style.color='#e9ecef';");
        button.setAttribute('onmouseout',"this.style.background='#e9ecef'; this.style.color='#495057';");
        return button;
    }

    mondaysInMonth(m,y) {

        var d = new Date(y,m,0),
        month = d.getMonth(),
        mondays = [];

        d.setDate(1);

        // Get the first Monday in the month
        while (d.getDay() !== 1) {
            d.setDate(d.getDate() + 1);
        }

        // Get all the other Mondays in the month
        while (d.getMonth() === month) {
            mondays.push(new Date(d.getTime()).getDate());
            d.setDate(d.getDate() + 7);
        }

       return mondays
    }

    sortObjectByKeys(o) {
        return Object.keys(o).sort().reduce((r, k) => (r[k] = o[k], r), {});
    }

    msToTime(duration) {
        var seconds = Math.floor((duration / 1000) % 60);
        var minutes = Math.floor((duration / (1000 * 60)) % 60);
        var hours = Math.floor((duration / (1000 * 60 * 60)) % 24);
      
        minutes = (minutes < 10) ? "0" + minutes : minutes;
        seconds = (seconds < 10) ? "0" + seconds : seconds;
      
        return (hours == 0) ? ((minutes == 0) ? seconds + "s" : minutes + "min " + seconds + "s" ): hours + "h " + minutes + "min " + seconds + "s";
    }

    getData(years, month_Number, mondays, allDay = false, sn = null){
        var res = {};
        for (const [key, value] of Object.entries(this.sortObjectByKeys(this.dataRecv))) {
            if(sn==null || key==sn){
                for (var i = 0; i < mondays.length; i++) {
                    var day = mondays[i];
                    value.forEach(element =>{
                        var start = new Date(Date.parse(element["start"]));
                        var end = new Date(Date.parse(element["end"]));
                        var time = end-start;
                        if(start.getFullYear() == years && start.getMonth()+1 == month_Number && start.getDate() >= day){
                            if(!allDay){
                                if(i==mondays.length-1 || start.getDate() < mondays[i+1]){  
                                    if(!(key in res)) res[key] = {};
                                    if(day in res[key]) res[key][day] += time;
                                    else res[key][day] = time;
                                }
                            }else if(sn==null){
                                if(i==mondays.length-1 || start.getDate() < mondays[i+1]){ 
                                    if(!(key in res)) res[key] = {};
                                    if(start.getDate() in res[key]) res[key][start.getDate()] += time;
                                    else res[key][start.getDate()] = time;
                                }
                            }else{
                                if(!(key in res)) res[key] = {};
                                if(start.getDate() in res[key]) res[key][start.getDate()] += time;
                                res[key][start.getDate()] = time;
                            }
                        }
                    });
                }
            }
        }
        return res;
    }

    render(){
        this.socketio.emit('data');
        if(this.reloaderData==null) this.reloaderData = setInterval(()=>{
            this.socketio.emit('data');
        },10000);
    }

    renderingChart(){

        var years = this.renderDay.getFullYear();
        var month_Number = this.renderDay.getMonth()+1;
        var mondays = this.mondaysInMonth(this.renderDay.getMonth()+1,this.renderDay.getFullYear());

        var monday = this.loadChartMonday

        var canvas = document.getElementById("myChart");

        if(canvas == null){
            var divCanvas = document.createElement('div');
            divCanvas.setAttribute('id', 'div_canvas');

            canvas = document.createElement('canvas');
            canvas.setAttribute('id', 'myChart');
            canvas.setAttribute('width', '800');
            canvas.setAttribute('height', '250');
            divCanvas.appendChild(canvas);
            this.element.appendChild(divCanvas);

            var style = document.createElement('style');
            style.setAttribute('type', 'text/css');
            style.appendChild(document.createTextNode(`/* Resume */ 
            #myChart{
                margin-top: 20px;
            }
            html, body {
                height: 100%;
                width: 100%;
                align-items: center;
                display: flex;
                justify-content: center;
            }
            #calendar{
                
            }
            #controls{ 
                bottom: -7px; 
                left: 0px; 
                position: absolute; 
            }
            #div_canvas{
                position: relative;
            }`.replace(/(            )/g, "")));
            document.head.appendChild(style);
        }

        var ctx = canvas.getContext("2d");

        var data = this.getData(years, month_Number, mondays,true)

        var days = [];
        var labelDays = [];

        if(Array.isArray(monday)){
            monday.forEach((m)=>{
                var date = new Date(years, month_Number-1,m);
                for(var day=0; day <=6 ; day++){
                    var actualDate = new Date(years, month_Number-1,date.getDate()+day);
                    days.push(actualDate);
                    if(actualDate.getDate()<10) var dd = "0"+actualDate.getDate();
                    else var dd = actualDate.getDate();
                    if(actualDate.getMonth()+1<10) var mm = "0"+(actualDate.getMonth()+1);
                    else var mm = actualDate.getMonth()+1;
                    labelDays.push(actualDate.getFullYear()+"-"+mm+"-"+dd);
                }
            });
        }else{ 
            var date = new Date(years, month_Number-1,monday);
            for(var day=0; day <=6 ; day++){
                var actualDate = new Date(years, month_Number-1,date.getDate()+day);
                days.push(actualDate);
                if(actualDate.getDate()<10) var dd = "0"+actualDate.getDate();
                else var dd = actualDate.getDate();
                if(actualDate.getMonth()+1<10) var mm = "0"+(actualDate.getMonth()+1);
                else var mm = actualDate.getMonth()+1;
                labelDays.push(actualDate.getFullYear()+"-"+mm+"-"+dd);
            }
        }

        var datasets = [];
        var cpt_sn = 0;
        var uniteTimeCoef;
        this.unitTime == "min" ? uniteTimeCoef = 60000 : uniteTimeCoef = 3600000;
        for (const [key, value] of Object.entries(data)) {

            if(!Array.isArray(monday)){
                var date = new Date(years, month_Number-1,monday);
                for (const dayNumber of Object.keys(value)) {
                    if(dayNumber<date.getDate()||dayNumber>date.getDate()+6) delete data[key][dayNumber];
                }
            }else{
                if(key!=this.loadChartSn) continue;
            }

            if(Object.keys(data[key]).length === 0){
                delete data[key];
            }else{
                var snData = [];
                var cpt = 0;
                days.forEach(day =>{
                    if(Object.keys(value).includes(day.getDate().toString())) snData.push({x:labelDays[cpt],y:value[day.getDate()]/uniteTimeCoef});
                    else snData.push({x:labelDays[cpt],y:NaN});
                    cpt++;
                });
                var sn = {
                    label: key,
                    borderColor: this.CHART_COLORS[Object.keys(this.CHART_COLORS)[cpt_sn]],
                    backgroundColor: this.CHART_COLORS[Object.keys(this.CHART_COLORS)[cpt_sn]].replace(/(1\))/g, "0.5)"),
                    borderWidth: 2,
                    data: snData
                };
                cpt_sn++;
                datasets.push(sn);
            }
        }

        var title;

        if(Array.isArray(monday)){
            title = "Résumé du mois de "+this.months[month_Number-1].toLowerCase()+" pour le robot '"+this.loadChartSn+"' :"
        }else{
            title = "Résumé de la semaine du lundi "+date.getDate()+" "+this.months[date.getMonth()].toLowerCase()+" "+date.getFullYear()+" :"
        }

        var unitTime = this.unitTime;

        var config = {
            type: 'bar',
            data: {
                labels: labelDays,
                datasets: datasets
            },
            options: {
                barValueSpacing: 20,
                responsive: true,
                title: {
                    display: true,
                    text: title
                },
                scales:{
                    xAxes: [{
                        type: "time",
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'DD/MM/YYYY'
                            }
                        },
                        scaleLabel: {
                            display: false,
                            labelString: 'Date'
                        },
                        offset: true
                    }],
                    yAxes: [{
                        scaleLabel: {
                            display: true,
                            labelString: "Temps ("+unitTime+")"
                        },
                        ticks: {
                            beginAtZero:true
                        }
                    }]
                },
                tooltips: {
                    callbacks: {
                        label: function(tooltipItem, data) {
                            var datasetLabel = data.datasets[tooltipItem.datasetIndex].label || '';
                            return datasetLabel + ' : ' + parseFloat(tooltipItem.yLabel.toFixed(2)) + unitTime[0];
                        },
                        title: function(tooltipItem, data) {
                            var date = new Date(Date.parse(tooltipItem[0].xLabel));
                            var week = new Array('Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche');
                            var months = new Array('Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre');
                            var str = week[date.getDay()]+" "+date.getDate()+" "+months[date.getMonth()].toLowerCase()+" "+date.getFullYear()+" :";
                            return str;
                        }
                    }
                }
            }
        }

        if(this.resume_chart!=undefined) this.resume_chart.destroy();
        
        this.resume_chart = new Chart(ctx, config);

        if(document.getElementById("controls")===null) {
            var controlsDiv = document.createElement("div");
            controlsDiv.setAttribute('id','controls');

            var button_min = this.buttonCreator('m', "btn_min", true, "z-index:2;");
            button_min.onclick = () => {
                this.unitTime = "min";
                this.renderingChart();
            }
            

            var button_heure = this.buttonCreator('h', "btn_heure", true, "z-index:2;");
            button_heure.onclick = () => {
                this.unitTime = "heure";
                this.renderingChart();
            }

            controlsDiv.appendChild(button_min);
            controlsDiv.appendChild(button_heure);
            divCanvas.appendChild(controlsDiv);
        }

    }
    
    rendering(){

        var today = this.renderDay
        
        var old_data = document.getElementById("calandar_data");
        if(old_data !==null) document.getElementById("calandar_data").remove();
        
        var month_Number = today.getMonth()+1;
        var years = today.getFullYear();

        if(month_Number<10) var mm = "0"+month_Number;
        else var mm = month_Number;

        var tabDiv = document.createElement("div");
        var tbl = document.createElement('table');
        tbl.setAttribute('class','table');
        tbl.style.width = '100%';
        var tbdy = document.createElement('tbody');

        var tHeader = document.createElement('thead');
        tHeader.setAttribute('id','thead');
        tHeader.setAttribute('class','thead-light');
        tbl.appendChild(tHeader);
        var trHeader = document.createElement('tr');
        var mondays = this.mondaysInMonth(month_Number,years);
        for (var i = 0; i <= mondays.length; i++) {
            var th = document.createElement('th');
            if(mondays[i-1]<10) var dd = "0"+mondays[i-1];
            else var dd = mondays[i-1];
            if(i==0){
                th.appendChild(document.createTextNode(""));
                th.setAttribute('style',"background-color: #fff; border-top: none; border-bottom: none;");
            }else{
                th.appendChild(document.createTextNode(dd+"/"+mm+"/"+years));
                th.onclick = (e) => {
                    this.loadChartMonday = e.currentTarget.textContent.split('/')[0]
                    this.loadChartSn = null;
                    this.renderingChart();
                }
                th.setAttribute('style', 'cursor: pointer;');
                th.setAttribute('onmouseover',"this.style.background='#495057'; this.style.color='#e9ecef';");
                th.setAttribute('onmouseout',"this.style.background=''; this.style.color='#495057';");
                th.setAttribute('scope','col');
            }
            trHeader.appendChild(th)
        }
        tHeader.appendChild(trHeader);

        var data = this.getData(years, month_Number, mondays);

        if(Object.keys(data).length == 0){
            var tr = document.createElement('tr');
            var thSN = document.createElement('th');
            thSN.appendChild(document.createTextNode("Pas de données pour ce mois"));
            thSN.setAttribute('style',"background-color: #fff; color: #495057; cursor: pointer;border-top: none");
            thSN.setAttribute('colspan',mondays.length+1);
            tr.appendChild(thSN);
            tbdy.appendChild(tr);
        }else{

            for (const key of Object.keys(data)) {
                var tr = document.createElement('tr');
                var thSN = document.createElement('th');
                thSN.appendChild(document.createTextNode(key));
                thSN.setAttribute('scope','row');
                thSN.setAttribute('style',"background-color: #e9ecef; color: #495057; cursor: pointer;");
                thSN.setAttribute('onmouseover',"this.style.background='#495057'; this.style.color='#e9ecef';");
                thSN.setAttribute('onmouseout',"this.style.background='#e9ecef'; this.style.color='#495057';");
                thSN.onclick = (e) => {
                    this.loadChartMonday = mondays;
                    this.loadChartSn = key;
                    this.renderingChart();
                }
                tr.appendChild(thSN);
                for (var i = 0; i < mondays.length; i++) {
                    var td = null;
                    
                    if(key in data) if(mondays[i] in data[key]){
                        td = document.createElement('td');
                        td.appendChild(document.createTextNode(this.msToTime(data[key][mondays[i]])));
                    }
                    
                    if(td == null){
                        td = document.createElement('td');
                        td.appendChild(document.createTextNode(""));
                    }
                    tr.appendChild(td);
                }
                tbdy.appendChild(tr);
            }

        }

        var div = document.getElementById("div_selector_calendar");

        if(div == null){

            var div = document.createElement('div');
            div.setAttribute('id', 'div_selector_calendar');
            div.setAttribute('style', 'margin-top: 10px;display: flex; align-items: center;justify-content: center;');

            var selector_calendar = document.createElement('input');
            selector_calendar.setAttribute('id', 'selector_calendar');
            selector_calendar.setAttribute('type', 'month');
            selector_calendar.setAttribute('value', years+"-"+mm);
            selector_calendar.addEventListener('change', (e) => {
                this.renderDay = new Date(Date.parse(e.target.value+"-01"));
                this.rendering();
            });

            var button_prev = this.buttonCreator('«', "prev", false, "margin-right: 5px;");
            button_prev.onclick = () => {
                var newDate = new Date(Date.parse(document.getElementById("selector_calendar").value+"-01"));
                newDate.setMonth(newDate.getMonth() - 1);
                this.loadChartMonday = this.mondaysInMonth(newDate.getMonth()+1,newDate.getFullYear())[0];
                this.renderDay = newDate;
                this.rendering();
            }
            
            var button_next = this.buttonCreator('»', "next", false, "margin-left: 5px;");
            button_next.onclick = () => {
                var newDate = new Date(Date.parse(document.getElementById("selector_calendar").value+"-01"));
                newDate.setMonth(newDate.getMonth() + 1);
                this.loadChartMonday = this.mondaysInMonth(newDate.getMonth()+1,newDate.getFullYear())[0];
                this.renderDay = newDate;
                this.rendering();
            }
            
            div.appendChild(button_prev);
            div.appendChild(selector_calendar);
            div.appendChild(button_next);

            this.element.appendChild(div);
        }
        
        document.getElementById("selector_calendar").setAttribute('value', years+"-"+mm);

        tbl.appendChild(tbdy);
        tabDiv.appendChild(tbl);

        tabDiv.setAttribute('id', "calandar_data");

        this.element.insertBefore(tabDiv, div);
        
        this.renderingChart();

    }

}
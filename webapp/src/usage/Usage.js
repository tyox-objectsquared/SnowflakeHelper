import React, {Component} from 'react';
import './usage.css';
import NavBar from "../nav/Nav";
import Octicon, {Search, Info} from '@githubprimer/octicons-react';
import {
    Chart,
    ChartLegend,
    ChartTitle,
    ChartSeries,
    ChartSeriesItem,
    ChartCategoryAxis,
    ChartCategoryAxisItem,
    ChartArea,
    ChartTooltip
} from '@progress/kendo-react-charts';
import {ReactComponent as LoadingRing} from '../doubleRing-200px.svg';
import 'hammerjs';
import {withRouter} from 'react-router-dom';
import API from '../api/API';


class Usage extends Component {

    constructor(props) {
        super(props);
        this.state = {loading: true};
    }


    handleResize = () => { //force chart to re-render when window is resized
        let temp = this.state.selectedDate;
        this.setState({selectedDate: null});
        this.setState({selectedDate: temp});
    };


    componentDidMount(): void { //private - requires authorization
        window.addEventListener('resize', this.handleResize);
        const api = new API();
        api.getHTTP("/usage", {},(data, statusCode) => {
            if (statusCode === 401) this.props.history.push('/login');
            else if (statusCode === 500) this.setState({loading: false, error: data}); //is an error
            else {
                this.setState({
                    loading: false,
                    dailyData: data,
                    months: Object.keys(data),
                    selectedMonth: Object.keys(data)[Object.keys(data).length - 1],
                    selectedDate: null
                });
            }
        });
    }


    renderSelector = (months: [], current_month: string) => {
        if (months.length === 0) {
            this.setState({error: "There is no usage data to display."});
            return null;
        } else {
            return (
                <div className="dropdown">
                    <button className="btn btn-secondary dropdown-toggle w-hundred" type="button" id="dropdownMenuButton"
                            data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">{current_month}</button>
                    <div className="dropdown-menu w-hundred" aria-labelledby="dropdownMenuButton">{
                        months.map( (month) => {return <div key={month} onClick={()=>this.setState({selectedMonth: month, selectedDate: null})} className="dropdown-item w-hundred">{month}</div>})
                    }
                    </div>
                </div>
            )
        }
    };


    renderList = (dailyData: {}, month: string, selectedDate: string) => {
        return Object.entries(dailyData).map(([date, data]) => {
            let hasPieChart = 'users' in data; //boolean
            return (
                <div className={"row table-row " + (date === selectedDate ? "selected-table-row " : "") + ( data['credits'] !== 0 ? "search-icon " : "")}
                     key={month+"/"+date} onClick={data['credits'] !== 0 ? ()=>this.updateDate(date): null}>
                    <div className="col-4">{month.split(",")[0]} {date}</div>
                    <div key={date} className="col-8">{data['credits']}
                    {data['credits'] !== 0 ?<Octicon icon={Search} />: null}
                    {data['credits'] !== 0 && 'users' in data ?<Octicon icon={Info} />: null}</div>
                    <div className="row">{selectedDate === date ? this.renderLineChart(Object.values(data['interval']), month.split(",")[0] + " " + date, hasPieChart) : null}</div>
                    <div className="row">{selectedDate === date && hasPieChart ? this.renderPieChart(data['users']) : null}</div>
                </div>
            )
        });
    };


    renderLineChart = (intervalData: [], date: string, hasPieChart: boolean) => {
        let offset = 35;
        if (hasPieChart) offset = 485;
        return (
            <Chart zoomable={false}>
                <ChartTitle text={"Usage on " + date} />
                <ChartTooltip format="{0}" />
                <ChartArea background={"#eff8ff"} width={document.getElementById("table-fragment").offsetWidth-offset}  height={400}/>
                <ChartCategoryAxis>
                    <ChartCategoryAxisItem title={{ text: 'Hour'}} categories={["12a",1,2,3,4,5,6,7,8,9,10,11,"12p",1,2,3,4,5,6,7,8,9,10,11]} />
                </ChartCategoryAxis>
                <ChartSeries>
                    <ChartSeriesItem color="#07425E" type="line" data={intervalData} />
                </ChartSeries>
            </Chart>
            );
    };


    renderPieChart = (data: {}) => {
        //Transform the data into the proper format
        const series = [];
        for (let user in data) {
            let item = {};
            item.user = user;
            item.share = data[user]['share'];
            item.time = data[user]['time'];
            series.push(item);
        }
        return (
        <Chart seriesColors={['#47758B', '#535B97', '#DBBC6A', '#DBA76A', '#DB826A', '#4C9C6F']}>
            <ChartTitle text={"Usage Time by User"} />
            <ChartLegend position="right"/>
            <ChartTooltip format={"{0}%"} />
            <ChartArea background={"#eff8ff"} width={450}  height={400}/>
            <ChartSeries>
                <ChartSeriesItem type="pie" data={series} field="share" categoryField="user" />
            </ChartSeries>
        </Chart>
        )};

    updateDate = (date: string) => { // closes chart view if you click on same date
        let newDate = null;
        if (date !== this.state.selectedDate) newDate = date;
        this.setState({selectedDate: newDate});
    };

    render() {
        const { loading, dailyData, months, selectedMonth, selectedDate, error } = this.state;
        return (
            <div className="container-fluid">
                <NavBar/>
                {!loading && !error ?
                    <div className="list container-fluid" id="table-fragment">
                        <div className="row">
                            <div className="col">{this.renderSelector(months, selectedMonth)}</div>
                        </div>
                        {selectedMonth != null ? this.renderList(dailyData[selectedMonth], selectedMonth, selectedDate) : null}
                    </div>: error ? <span className="alert alert-danger">{error}</span>: <div className="ring-container" style={{marginTop: "100px"}}><LoadingRing /></div>}
            </div>
        )
    }
}
export default withRouter(Usage);
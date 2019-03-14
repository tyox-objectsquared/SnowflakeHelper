import React, { Component } from 'react';
import {Chart, ChartLegend, ChartSeries, ChartSeriesItem, ChartArea} from '@progress/kendo-react-charts'
import './usage.css';


const series = [
    { category: 'Eaten', value: 0.42 },
    { category: 'Not eaten', value: 0.58 }
];

class Usage extends Component {


    ChartContainer = () => (
        <Chart seriesColors={['orange', '#ffe']}>
            <ChartArea height={500} background="#eee" margin={30} />
            <ChartLegend position="top" />
            <ChartSeries>
                <ChartSeriesItem type="pie" data={series} field="value" categoryField="category" />
            </ChartSeries>
        </Chart>
    );

    render() {
        return (
            <div className="container-fluid">
            <this.ChartContainer />
            </div>
        )
    }
}

export default Usage;

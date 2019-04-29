import React, {Component, Fragment} from 'react';
import './queries.css';
import {Query} from './Query';
import NavBar from "../nav/Nav";
import Octicon, {Check, Sync, IssueOpened, Shield, ListUnordered, Ellipsis} from '@githubprimer/octicons-react';
import ReactTooltip from 'react-tooltip'
import sqlFormatter from "sql-formatter";
import {withRouter} from 'react-router-dom';
import API from '../api/API';
class Queries extends Component {

    statusMap = {
        "BLOCKED": { icon: Shield, text: "Blocked", color: "Red" },
        "FAILED_WITH_ERROR": { icon: IssueOpened, text: "", color: "Red" },
        "FAILED_WITH_INCIDENT": { icon: IssueOpened, text: "Failed", color: "Red" },
        "QUEUED": { icon: ListUnordered, text: "Queued", color: "DarkBlue" },
        "RESUMING_WAREHOUSE": { icon: Ellipsis, text: "Resuming Warehouse", color: "DarkBlue"},
        "RUNNING": {icon: Sync, text: "Running", color: "DarkBlue" },
        "SUCCESS": {icon: Check, text: "Success", color: "Green" }
    };

    intervalsMap = {
        15: "15 minutes",
        30: "30 minutes",
        60: "1 hour",
        120: "2 hours",
        240: "4 hours",
        480: "8 hours",
        720: "12 hours",
        1440: "24 hours"
    };

    constructor(props) {
        super(props);
        this.state = {loading: true, queryData: null, numMinutes: 30, queriedMinutes: 30};
    }

    componentDidMount(): void {
        this.getQueries(this.state.numMinutes);
    }

    update(): void {
        this.setState({loading: true, queryData: null});
        this.getQueries(this.state.numMinutes);
    }

    getQueries = (numMinutes) => { //private - requires authorization
        this.setState({queriedMinutes: numMinutes});
        const api = new API();
        api.getHTTP("http://localhost:5000/queries?numMinutes="+numMinutes, (data, statusCode: number) => {
            if (statusCode === 401) this.props.history.push('/login');
            else if (statusCode / 500 >= 1) this.setState({loading: false, error: data}); //is an error
            else {
                const queries = [];
                for (var i=0; i < data.length; ++i) {
                    queries.push(new Query(
                        data[i].QUERY_ID,
                        data[i].EXECUTION_STATUS,
                        data[i].QUERY_TEXT,
                        data[i].USER_NAME,
                        data[i].ERROR_CODE,
                        data[i].ERROR_MESSAGE,
                        Queries.formatDateTime(new Date(data[i].START_TIME)),
                        Queries.formatDateTime(new Date(data[i].END_TIME)),
                        data[i].TOTAL_ELAPSED_TIME));
                }
                this.setState({loading: false, queryData: queries});
            }
        });
    };


    stop_query(id: string) { //private - requires authorization
        const api = new API();
        api.postHTTP("http://localhost:5000/queries/stop?id=" + id, null, (data, statusCode) => {
            if (statusCode === 401) this.props.history.push('/login');
            else if (statusCode / 500 >= 1) this.setState({loading: false, error: data}); //is an error
            else {
                let queries = this.state.queryData;
                for (let i=0; i< queries.length; ++i) {
                    if (queries[i].query_id === id) {
                        queries[i].execution_status = data['status'];
                        if (data['message'] !== 'Identified SQL statement is not currently executing.') {
                            queries[i].error_message =  data['error_message'];
                            queries[i].error_code = data['error_code'];
                            queries[i].start_time = Queries.formatDateTime(new Date(data['start_time']));
                            queries[i].end_time = Queries.formatDateTime(new Date(data['end_time']));
                        }
                    }
                }
                this.setState({queryData: queries});
            }
        });
    }

    static formatDateTime(date: Date) {
        let date_string = "";
        const today: Date = new Date();
        if ((date.getFullYear() !== today.getFullYear() || date.getMonth() !== today.getMonth())
            || date.getDate() !== today.getDate()) {
            date_string += date.toLocaleDateString("en-US") + " ";
        }
        date_string += date.toLocaleTimeString("en-US");
        return date_string;
    }

    renderQueries = (queryData: Query[]) => {
        if ('error' in this.state) {
            return (
                <div className="row table-row">
                    <div className="col" data-tip={this.state.error}>{ this.state.error }</div>
                    <ReactTooltip html={true} effect="solid" type="error" delayShow={500} />
                </div>
            )
        }
        if (queryData.length === 0) {
            const {numMinutes, queriedMinutes} = this.state;
            if (numMinutes === queriedMinutes) {
                return (
                    <div className="row table-row">
                        <div className="col" data-tip={"There are no queries from the past " + this.intervalsMap[numMinutes] + "."}>{"There are no queries from the past " + this.intervalsMap[numMinutes] + "."}</div>
                        <ReactTooltip html={true} effect="solid" type="info" delayShow={500} />
                    </div>
                )
            } else {
                return (
                    <div className="row table-row">
                        <div className="col" data-tip={"Press Refresh to see queries within a different interval."}>Press Refresh to see queries within a different interval.</div>
                        <ReactTooltip html={true} effect="solid" type="info" delayShow={500} />
                    </div>
                )
            }
        }
        return queryData.map((query) => {
            let formatted_status = this.statusMap[query.execution_status].text;
            if (query.execution_status === "FAILED_WITH_ERROR") {
                formatted_status += "Failed with Error Code " + query.error_code + ": " + query.error_message;
            }
            let formatted_sql: string = sqlFormatter.format(query.sql_text);
            formatted_sql = formatted_sql.replace(/(?:\r\n|\r|\n)/g, '<br>');
            return (
                <div key={query.query_id} className="row table-row">
                    <div className="col-1 status">
                        <div  style={{width: "30px", color: this.statusMap[query.execution_status].color}} data-tip={"<div>" + formatted_status + "</div>"}><Octicon icon={this.statusMap[query.execution_status].icon} /></div>
                        <div>{formatted_status === "Running" ? <div onClick={() => this.stop_query(query.query_id)} style={{"height": "27px", "paddingTop": 0, "paddingBottom": 0, "cursor": "pointer"}} className={"btn btn-danger"}>Stop</div> : null}</div>
                    </div>
                    <div className="col-4 sql" data-tip={"<div>" + formatted_sql +"</div>"} >{query.sql_text}</div>
                    <div className="col-1" data-tip={"<div>" + query.username + "</div>"}>{query.username}</div>
                    <div className="col-2" data-tip={"<div>" + query.start_time + "</div>"}>{query.start_time}</div>
                    <div className="col-2" data-tip={"<div>" + query.end_time + "</div>"}>{query.end_time}</div>
                    <div className="col-1" data-tip={"<div>" + query.total_elapsed_time + "</div>"}>{query.total_elapsed_time}</div>
                    <ReactTooltip html={true} effect="solid" type="info" delayShow={500} />
                </div>
            );
        });
    };

    render() {
        const { loading, queryData, numMinutes} = this.state;
        return (
            <div className="container-fluid">
                <NavBar/>
                <div className="list container-fluid">
                    <div className="row table-header">
                        <div className="col-1">Status</div>
                        <div className="col-2">SQL Text</div>
                        <div className="col-2 dropdown">
                            <button style={{padding: "0 15px 0 15px"}} className="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton"
                                    data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">{this.intervalsMap[numMinutes]}</button>
                            <div className="dropdown-menu" aria-labelledby="dropdownMenuButton">
                                {Object.entries(this.intervalsMap).map(([numMins, interval]) => <div key={numMins} onClick={()=>this.setState({numMinutes: numMins})} className="dropdown-item">{interval}</div>)}
                            </div>
                        </div>
                        <div className="col-1">User</div>
                        <div className="col-2">Start Time</div>
                        <div className="col-2">End Time</div>
                        <div className="col-1">Elapsed Time</div>
                        <div className="col-1 btn btn-outline-light" onClick={() => this.update()} style={{"height": "27px", "paddingTop": 0, "paddingBottom": 0, "cursor": "pointer"}}>Refresh <Octicon icon={Sync} /></div>
                    </div>
                    <Fragment>{loading ? "Loading..." : this.renderQueries(queryData)}</Fragment>
                </div>
            </div>
        );
    }
}

export default withRouter(Queries);

export class Query {
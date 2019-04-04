import React, {Component, Fragment} from 'react';
import './queries.css';
import {Query} from './Query';
import NavBar from "../nav/Nav";
import Octicon, {Check, Sync, IssueOpened, Shield, ListUnordered, Ellipsis} from '@githubprimer/octicons-react';
import ReactTooltip from 'react-tooltip'
import sqlFormatter from "sql-formatter";
import {auth} from '../index'
const request = require('request');

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

    constructor(props) {
        super(props);
        this.state = {loading: true, queryData: null};
    }

    componentDidMount(): void {
        this.getQueries();
    }

    update(): void {
        this.setState({loading: true, queryData: null});
        this.getQueries();
    }

    getQueries = () => { //private - requires authorization
        request.get({
            url: "http://localhost:5000/queries",
            headers: {'content-type': 'application/json', 'Authorization': auth.authorizationHeader}
        }, (error, response, body) => {
            if (!error && response.statusCode === 200) {
                const data = JSON.parse(body);
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
            } else {
                if (error === null) error = response.statusCode + ": " + response.statusMessage;
                this.setState({loading: false, error: error.toString()})
            }
        });
    };

    stop_query(id: string) { //private - requires authorization
        request.post({
            url: "http://localhost:5000/queries/stop/" + id,
            headers: {'content-type': 'application/json', 'Authorization': auth.authorizationHeader}
        }, (error, response, body) => {
            if (!error && response.statusCode === 200) {
                const data = JSON.parse(body);
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
            } else {
                if (error === null) error = response.statusCode + ": " + response.statusMessage;
                this.setState({loading: false, error: error.toString()})
            }
        });
    }

    static formatDateTime(date: Date) {
        let date_string = "";
        const today: Date = new Date();
        if (date.getFullYear() !== today.getFullYear() || date.getMonth() !== today.getMonth() || date.getDate() !== today.getDate()) {
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
            return (
                <div className="row table-row">
                    <div className="col" data-tip={"There are no queries from the past 30 minutes."}>There are no queries from the past 30 minutes.</div>
                    <ReactTooltip html={true} effect="solid" type="info" delayShow={500} />
                </div>
            )
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
        const { loading, queryData} = this.state;
        return (
            <div className="container-fluid">
                <NavBar/>
                <div className="list container-fluid">
                    <div className="row table-header">
                        <div className="col-1">Status</div>
                        <div className="col-4">SQL Text</div>
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

export default Queries;

import React, { Component } from 'react';
import './queries.css';

class Queries extends Component {
    render() {
        return (
            <div className="container-fluid">
                <div className="row">
                    <div className="col-1 card-header">Status</div>
                    <div className="col-6 card-header">SQL Text</div>
                    <div className="col-2 card-header">User</div>
                    <div className="col-1 card-header">Start Time</div>
                    <div className="col-1 card-header">End Time</div>
                    <div className="col-1 card-header">Elapsed Time</div>
                </div>
            </div>
        );
    }
}

export default Queries;

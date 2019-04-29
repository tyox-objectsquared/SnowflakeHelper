import React, {Component} from 'react';
import './account.css';
import {withRouter} from "react-router-dom";
import API from "../api/API";
import Account from "./Account";
import {ReactComponent as LoadingRing} from "../doubleRing-50px.svg";

class ChangeEmail extends Component {

    constructor(props) {
        super(props);
        this.state = {loading: false};
    }

    componentDidMount(): void {
        const email = Account.accountService.emailAddress;
        if (email) this.setState({emailAddress: email});
    }

    updateEmail = (email: string) => {
        const api = new API();
        this.setState({loading: true});
        api.postHTTP("http://localhost:5000/update-email",{}, {username: Account.accountService.username, emailAddress: email}, (data, statusCode) => {
            if (statusCode === 401) this.props.history.push('/login');
            else if (statusCode === 500) this.setState({emailStatus: "failure", emailMessage: data});
            else if (statusCode === 200){
                this.setState({emailStatus: data.status, emailMessage: data.message, loading: false});
                Account.accountService.emailAddress = email;
                localStorage.setItem("EMAIL", email);
                if (data.status === "success") Account.accountService.ee.emit('AccountEvent', {comp: 'info', message: "Email has been updated successfully.", email: email}, false)
            }
        });
    };

    render() {
        const {emailMessage, emailStatus, emailAddress, loading} = this.state;
        return (
            <div className="card">
                <div className="card-body">
                    <h4 className="card-title">Add Email Address</h4>
                    <div className="form-group">
                        <label>Email Address</label>
                        <input onChange={(event) => this.setState({emailAddress: event.target.value})} type="email" className="form-control" placeholder="Email Address" value={emailAddress ? emailAddress: ""}/>
                    </div>
                    <button className="btn btn-primary form-group" onClick={() => this.updateEmail(emailAddress)}
                            disabled={/[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?/.test(emailAddress)? null : true}>Update</button>
                    <button className="btn btn-outline-primary form-group" onClick={() => Account.accountService.ee.emit('AccountEvent', {comp: 'info', message: null}, false)}>Cancel</button>
                    {loading ? <div className="ring-container"><LoadingRing/></div> : null}
                    {emailMessage ? <span className={emailStatus === "success" ? "alert alert-success": "alert alert-danger"}>{emailMessage}</span>: null}
                </div>
            </div>
        );
    }
} export default withRouter(ChangeEmail);

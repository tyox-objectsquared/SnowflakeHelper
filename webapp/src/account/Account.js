import React, {Component} from 'react';
import './account.css';
import {withRouter} from "react-router-dom";
import NavBar from "../nav/Nav";
import {ReactComponent as LoadingRing} from '../doubleRing-200px.svg';
import ChangePassword from "./ChangePassword";
import ChangeEmail from "./ChangeEmail";
import {EventEmitter} from "events";
import API from "../api/API";

class Account extends Component {

    static accountService = {
        ee: new EventEmitter(),
        firstName: null,
        lastName: null,
        emailAddress: null,
        loginName: null,
        username: null
    };

    constructor(props) {
        super(props);
        this.state = {comp: "info", loading: true};
        Account.accountService.ee.on('AccountEvent', (data) => {
            this.setState({comp: data.comp, message: data.message});
            if (data.hasOwnProperty('email')) this.setState({emailAddress: data.email});
        });
    }

    componentDidMount(): void {
        const api = new API();
        api.getHTTP("/account-info", {username: localStorage.getItem("username")}, (data, statusCode) => {
            if (statusCode === 401) this.props.history.push('/login');
            else if (statusCode === 500) this.setState({error: data, loading: false});
            else if (statusCode === 200) {
                Account.accountService.firstName = data.FIRST_NAME;
                Account.accountService.lastName = data.LAST_NAME;
                Account.accountService.emailAddress = data.EMAIL;
                Account.accountService.loginName = data.LOGIN_NAME;
                Account.accountService.username = data.NAME;
                this.setState({firstName: data.FIRST_NAME, lastName: data.LAST_NAME, emailAddress: data.EMAIL, loginName: data.LOGIN_NAME, username: data.NAME, loading: false});
            }
        });
    }

    render() {
        const {comp, message, firstName, lastName, emailAddress, loading, loginName, error } = this.state;
        return (
            <div className="container-fluid">
                <NavBar/>
                <div className="container">
                    {comp === "info" && (!loading && !error)? <div className="card">
                        <div className="card-body">
                            <h4 className="card-title">User Information</h4>
                            <div className="row">
                                <div className="label col-3">User</div>
                                <div className="col">{loginName}</div>
                            </div>
                            <div className="row">
                                <div className="label col-3">First Name</div>
                                <div className="col">{firstName}</div>
                            </div>
                            <div className="row">
                                <div className="label col-3">Last Name</div>
                                <div className="col">{lastName}</div>
                            </div>
                            <div className="row">
                                <div className="label col-3">Password</div>
                                <div className="col"><button onClick={() => this.setState({comp: "pwd"})} className="btn-primary">Change Password</button></div>
                            </div>
                            <div className="row">
                                <div className="label col-3">Email</div>
                                <div className="col">
                                    {emailAddress ? <span style={{marginRight: "30px"}}>{emailAddress}</span> : null}
                                    <button onClick={() => this.setState({comp: "email"})} className="btn-primary">{emailAddress ? "Update Email" : "Add Email"}</button>
                                </div>
                            </div>
                        </div>
                    </div> :
                        comp === "pwd" ? <ChangePassword/> :
                        comp === "email" ? <ChangeEmail/> :
                        error ? <span className="alert alert-danger">{error}</span>: <div className="ring-container"  style={{marginTop: "100px"}}><LoadingRing/></div>}
                    {message ? <span className="alert alert-success">{message}</span>: null}
                </div>
            </div>
            );
    }
} export default withRouter(Account);

import React, {Component} from 'react';
import './account.css';
import {withRouter} from "react-router-dom";
import API from "../api/API";
import Account from "./Account";
import {ReactComponent as LoadingRing} from '../doubleRing-50px.svg';

class ChangePassword extends Component {

    constructor(props) {
        super(props);
        this.state = {isPasswordValid: false, loading: false};
    }

    matchPwd = (pw1, pw2) => {
        let status = pw1 === pw2 ? "success": "failure";
        let message = pw1 === pw2 ? "Passwords match.": "Passwords do not match.";
        this.setState({passwordMessage: message, passwordStatus: status});
        return pw1 === pw2;
    };

    validatePwd = (str) => {
        let message = null;
        let status = "failure";
        if (!str) return null;
        else if (str.length < 8) message = "ChangePassword must be at least 8 characters long.";
        else if (str.length > 256) message = "ChangePassword must be less than 256 characters long.";
        else if (str.search(/\d/) === -1) message = "ChangePassword must contain a digit.";
        else if (str.search(/[A-Z]/) === -1) message = "ChangePassword must contain an uppercase letter.";
        else if (str.search(/[a-z]/) === -1) message = "ChangePassword must contain a lowercase letter.";
        else if (str.search(/[^a-zA-Z0-9!@#$%^&*()_+]/) !== -1) message = "ChangePassword contains an invalid character.";
        else {
            status = "success";
            message = "New password is valid."
        }
        this.setState({passwordMessage: message, passwordStatus: status});
        return status === "success";
    };

    updatePassword = (oldP, newP) => {
        const api = new API();
        this.setState({passwordMessage: null, loading: true});
        api.postHTTP("http://localhost:5000/update-password", {}, {loginName: Account.accountService.loginName, username: Account.accountService.username, oldP: oldP, newP: newP}, (data, statusCode) => {
            if (statusCode === 401) this.props.history.push('/login');
            else if (statusCode === 500) this.setState({passwordStatus: "failure", passwordMessage: data});
            else if (statusCode === 200) {
                let passMessage = data.message;
                if (passMessage.includes("Incorrect username or password was specified.")) passMessage = "Incorrect username or password was specified.";
                else if (passMessage.includes("PRIOR_USE")) passMessage = "Please create a new password that you have not used in the past.";
                this.setState({passwordStatus: data.status, passwordMessage: passMessage, loading: false});
                if (data.status === "success") Account.accountService.ee.emit('AccountEvent', {comp:'info', message: "Password has been updated successfully."});
            }
        });
    };

    render() {
        const {passwordMessage, passwordStatus, oldP, newP, isPasswordValid, doPasswordsMatch, loading} = this.state;
        return (
            <div className="card">
                <div className="card-body">
                    <h4 className="card-title">Change Password</h4>
                    <div className="form-group">
                        <label>Current Password</label>
                        <input onChange={(event) => this.setState({oldP: event.target.value})} type="password" className="form-control" placeholder="Current Password" />
                    </div>
                    <div className="form-group">
                        <label>New Password</label>
                        <input onChange={(event) => this.setState({newP: event.target.value, isPasswordValid: this.validatePwd(event.target.value)})} type="password" className="form-control" placeholder="New Password" />
                    </div>
                    <div className="form-group">
                        <label>Confirm New Password</label>
                        <input onChange={(event) => this.setState({confirmP: event.target.value, doPasswordsMatch: isPasswordValid && this.matchPwd(newP, event.target.value)})} type="password" className="form-control" placeholder="Confirm New Password" />
                    </div>
                    <button className="btn btn-primary form-group" onClick={() => this.updatePassword(oldP, newP)} disabled={ !oldP || !(isPasswordValid && doPasswordsMatch) ? true : null}>Change</button>
                    <button className="btn btn-outline-primary form-group" onClick={() => Account.accountService.ee.emit('AccountEvent', {comp:'info', message: null}, false)}>Cancel</button>
                    {loading ? <div className="ring-container"><LoadingRing/></div> : null}
                    {passwordMessage ? <span className={passwordStatus === "success" ? "alert alert-success": "alert alert-danger"}>{passwordMessage}</span>: null}
                </div>
            </div>
        );
    }

} export default withRouter(ChangePassword);
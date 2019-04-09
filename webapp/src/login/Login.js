import {Redirect, withRouter} from "react-router-dom";
import NavBar from "../nav/Nav";
import React, {Component} from "react";
import App from "../App";

class Login extends Component {
    constructor(props) {
        super(props);
        this.state = {redirectToReferrer: false, message: App.authService.message, account: "", username: "", password: ""};
    }

    login = (username, password, account) => {
        App.authService.authenticate(username, password, account, (isAuthenticated, message) => {
            if (isAuthenticated) this.setState({redirectToReferrer: true});
            else this.setState({message: message})
        });
    };

    render() {
        const { from } = this.props.location.state || { from: { pathname: "/usage" } };
        const { error, redirectToReferrer, account, username, password, message } = this.state;
        if (redirectToReferrer || App.authService.isAuthenticated === "yes") return <Redirect to={from} />;
        return (
            <div className="container-fluid">
                { error == null ?
                    <div>
                        <NavBar/>
                        <div className="container">
                            <div className="form-group">
                                <label>Account Name <span style={{color: "#aaaaaa"}}>(xx00000)</span></label>
                                <input onChange={(event) => this.setState({account: event.target.value})} type="text" className="form-control" placeholder="Account Name" />
                            </div>
                            <div className="form-group">
                                <label>Username</label>
                                <input onChange={(event) => this.setState({username: event.target.value})} type="text" className="form-control" placeholder="Username" />
                            </div>
                            <div className="form-group">
                                <label>Password</label>
                                <input onChange={(event) => this.setState({password: event.target.value})} type="password" className="form-control" placeholder="Password" />
                            </div>
                            <button onClick={() => this.login(this.state.username, this.state.password, this.state.account)} disabled={(! /[A-Za-z]{2}\d{5}/.test(account) || username === "") || password === ""} className="btn btn-primary form-group">Submit</button>
                            {message ? <div className="alert alert-danger">{this.state.message}</div> : null}
                        </div>
                    </div> : <div className="alert alert-danger">Cannot connect to server.</div>}
            </div>
        );
    }
} export default withRouter(Login);
import React, {Component} from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import Queries from './queries/Queries'
import Usage from './usage/Usage'
import { BrowserRouter, Route, Switch, Redirect} from 'react-router-dom';
import * as serviceWorker from './serviceWorker';
import 'bootstrap/dist/js/bootstrap.bundle.js';
import NavBar from "./nav/Nav";
const request = require('request');


export const auth = {
    isAuthenticated: localStorage.getItem('isAuth'),
    authorizationHeader: localStorage.getItem('auth_token'),
    message: null,
    authenticate(username, password, account, cb) {
        request.post({
            url: 'http://localhost:5000/login',
            body: [username, password, account],
            json: true
        }, (error, response, body) => {
            if (!error && response.statusCode === 200) {
                this.isAuthenticated = body['isAuth'] ? "yes" : "no";
                localStorage.setItem('isAuth', this.isAuthenticated);
                if (body.hasOwnProperty('auth_token')) {
                    this.authorizationHeader = body['auth_token'];
                    localStorage.setItem('auth_token', this.authorizationHeader);
                } else {
                    localStorage.clear();
                    this.message = body['message'];
                }
                cb(this.isAuthenticated, this.message);
            }
        });
    },
    logout(username, cb) { //handled locally
        this.isAuthenticated = false;
        localStorage.clear();
    }};


class Login extends Component {
    constructor(props) {
        super(props);
        this.state = {loading: true, redirectToReferrer: false};
    }
    componentDidMount(): void { //public
        request.get({
            url: "http://localhost:5000/coops",
            headers: {'content-type': 'application/json'}
        }, (error, response, body) => {
            if (!error && response.statusCode === 200) {
                const data = JSON.parse(body);
                this.setState({loading: false, coops: data});
            } else {
                this.setState({loading: false, error: error.toString()})
            }
        });
    }

    login = (username, password, account) => {
        auth.authenticate(username, password, account, (isAuthenticated, message) => {
            if (isAuthenticated) this.setState({redirectToReferrer: true});
            else this.setState({message: message})
        });
    };

    render() {
        const { from } = this.props.location.state || { from: { pathname: "/usage" } };
        const {loading, coops, error, redirectToReferrer} = this.state;
        if (redirectToReferrer || auth.isAuthenticated) return <Redirect to={from} />;
        return (
            <div className="container-fluid">
                {!loading && !error ?
                    <div>
                        <NavBar/>
                        <div className="container">
                            <div className="form-group">
                                <label>Coop</label>
                                <select onChange={(event) => this.setState({coop: event.target.value})} className="form-control">
                                    <option key="select" value="select" >Select</option>
                                    {Object.entries(coops).map( ([name, account]) => {
                                        return (<option key={account} value={account}>{name}</option>)
                                    })}
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Username</label>
                                <input onChange={(event) => this.setState({username: event.target.value})} type="text" className="form-control" placeholder="Username" />
                            </div>
                            <div className="form-group">
                                <label>Password</label>
                                <input onChange={(event) => this.setState({password: event.target.value})} type="password" className="form-control" placeholder="Password" />
                            </div>
                            <button onClick={() => this.login(this.state.username, this.state.password, this.state.coop)} disabled={this.state.coop === undefined || this.state.coop === "select" ? true: null} className="btn btn-primary form-group">Submit</button>
                            {this.state.hasOwnProperty('message') ? <div className="alert alert-danger">{this.state.message}</div> : null}
                        </div>
                    </div> : !loading && error !== null ? <div className="alert alert-danger">Cannot connect to server.</div> : null}
            </div>
        );
    }
}


//https://reacttraining.com/react-router/web/example/auth-workflow
const PrivateRoute = ({ component: Component, ...rest }) => (
    <Route {...rest} render={props =>
        auth.isAuthenticated === "yes" ?
            <Component {...props} /> :
            <Redirect to={{pathname: "/login", state: {from: props.location}}}/>
    }/>);

const LoginRoute = ({ component: Component, ...rest }) => ( //reversed form of private route
    <Route {...rest} render={props =>
        auth.isAuthenticated === "yes" ?
            <Redirect to={{pathname: "/usage", state: {from: props.location}}}/> :
            <Component {...props} />
    }/>);

console.log(auth);
ReactDOM.render(
    <div>
        <BrowserRouter>
            <Switch>
                <PrivateRoute exact path='/queries' component={Queries}/>
                <PrivateRoute exact path='/usage' component={Usage}/>
                <LoginRoute exact path='/login' component={Login}/>
                />} />
            </Switch>
        </BrowserRouter>
    </div>
, document.getElementById('root'));

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();

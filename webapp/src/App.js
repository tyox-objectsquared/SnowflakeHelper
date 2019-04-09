import React, {Component} from 'react';
import './index.css';
import Queries from './queries/Queries';
import Usage from './usage/Usage';
import Login from './login/Login';
import { BrowserRouter, Route, Switch, Redirect} from 'react-router-dom';
import 'bootstrap/dist/js/bootstrap.bundle.js';
import API from './api/API';

class App extends Component {


    static authService = {
        isAuthenticated: localStorage.getItem('isAuth'),
        authorizationHeader: localStorage.getItem('auth_token'),
        message: null,
        authenticate(username, password, account, cb) {
            const payload = {username: username, password: password, account: account};
            const api = new API();
            api.postHTTP('http://localhost:5000/login', payload,(data, statusCode) => {
                if (statusCode === 401) this.props.history.push('/login');
                else if (statusCode / 500 >= 1) this.setState({loading: false, error: data}); //is an error
                else {
                    this.isAuthenticated = data['isAuth'] ? "yes" : "no";
                    localStorage.setItem('isAuth', this.isAuthenticated);
                    if (data.hasOwnProperty('auth_token')) {
                        this.authorizationHeader = data['auth_token'];
                        this.message = null;
                        localStorage.setItem('auth_token', this.authorizationHeader);
                    }
                    cb(this.isAuthenticated, this.message);
                }
            });
        },
        logout(message) { //handled locally
            this.isAuthenticated = "no";
            localStorage.clear();
            if (message === "authorization token expired") this.message = "Session expired. Please login again.";
        }
    };


    render() {
        return (
            <div>
                <BrowserRouter>
                    <Switch>
                        <PrivateRoute exact path='/queries' component={Queries}/>
                        <PrivateRoute exact path='/usage' component={Usage}/>
                        <LoginRoute exact path='/login' component={Login}/>
                    </Switch>
                </BrowserRouter>
            </div>
        );
    }


}
export default App;

//https://reacttraining.com/react-router/web/example/auth-workflow
const PrivateRoute = ({ component: Component, ...rest }) => (
    <Route {...rest} render={props =>
        App.authService.isAuthenticated === "yes" ?
            <Component {...props} /> :
            <Redirect to={{pathname: "/login", state: {from: props.location}}}/>
    }/>);

const LoginRoute = ({ component: Component, ...rest }) => ( //reversed form of private route
    <Route {...rest} render={props =>
        App.authService.isAuthenticated === "yes" ?
            <Redirect to={{pathname: "/usage", state: {from: props.location}}}/> :
            <Component {...props} />
    }/>);


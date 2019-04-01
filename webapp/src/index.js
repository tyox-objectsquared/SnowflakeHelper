import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import Queries from './queries/Queries'
import Usage from './usage/Usage'
import { BrowserRouter, Route, Switch } from 'react-router-dom';
import * as serviceWorker from './serviceWorker';
import 'bootstrap/dist/js/bootstrap.bundle.js';

ReactDOM.render(
    <div>
        <BrowserRouter>
            <Switch>
                <Route exact path='/queries' component={Queries}/>
                <Route exact path='/usage' component={Usage}/>
            </Switch>
        </BrowserRouter>
    </div>
, document.getElementById('root'));

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();

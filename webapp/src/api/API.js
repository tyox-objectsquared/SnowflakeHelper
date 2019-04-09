import {Component} from 'react';
import App from "../App";
const request = require("request");

class API extends Component {

    static handleResponse(error, response, body, cb) {
        if (error) cb(error, 500);
        else if (response) {
            if (response.statusCode === 401) {
                App.authService.logout(body);
                cb(response.statusMessage, response.statusCode);
            }
            else if (response.statusCode === 200) {
                cb(body, response.statusCode);
                if (response.headers.hasOwnProperty('auth_token')) localStorage.setItem('auth_token', response.headers.auth_token);
            }
        }
    }


    getHTTP(url: string, cb) {
        request.get({
            url: url,
            json: true,
            headers: {'content-type': 'application/json', 'Authorization': App.authService.authorizationHeader}
        }, (error, response, body) => {
            API.handleResponse(error, response, body, cb)
        });
    }


    postHTTP(url: string, payload: Object, cb) {
        request.post({
            url: url,
            body: payload,
            json: true,
            headers: {'content-type': 'application/json', 'Authorization': App.authService.authorizationHeader}
        }, (error, response, body) => {
            API.handleResponse(error, response, body, cb)
        });
    }
}
export default API;

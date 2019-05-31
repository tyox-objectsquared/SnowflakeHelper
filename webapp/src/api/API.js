import {Component} from 'react';
import App from "../App";
const request = require("request");

class API extends Component {

    AWS_URL = "http://snowflakehelper.sedatasp.com:5000";

    static handleResponse(error, response, body, cb) {
        if (error) cb(error.toString(), 500);
        else if (response) {
            if (response.statusCode === 500) cb(body, 500);
            else if (response.statusCode === 401) {
                App.authService.logout(body);
                let message = response.statusMessage;
                if (body.hasOwnProperty('data') && body['data'].hasOwnProperty('message')) message = body['data']['message'];
                cb(message, response.statusCode);
            }
            else if (response.statusCode === 200) {
                localStorage.setItem('auth_token', body['auth_token']);
                App.authService.authorizationHeader = body['auth_token'];
                if (body.hasOwnProperty('userData')) {
                    Object.entries(body['userData']).forEach( ([key, value]) => {
                        localStorage.setItem(key, value);
                    });
                }
                cb(body['data'], response.statusCode);
            }
        }
    }


    getHTTP(endpoint: string, qs: {}, cb) {
        qs.start_date = (new Date().getTime() / 1000) | 0; //truncate decimal
        request.get({
            url: this.AWS_URL + endpoint,
            json: true,
            qs: qs,
            headers: {'content-type': 'application/json', 'Authorization': App.authService.authorizationHeader}
        }, (error, response, body) => {
            API.handleResponse(error, response, body, cb)
        });
    }


    postHTTP(endpoint: string,  qs: {}, payload: Object, cb) {
        qs.start_date = (new Date().getTime() / 1000) | 0; //truncate decimal
        request.post({
            url: this.AWS_URL + endpoint,
            body: payload,
            json: true,
            qs: qs,
            headers: {'content-type': 'application/json', 'Authorization': App.authService.authorizationHeader, 'Timestamp': Date.now()}
        }, (error, response, body) => {
            API.handleResponse(error, response, body, cb)
        });
    }
}
export default API;

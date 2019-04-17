import {Component} from 'react';
import App from "../App";
const request = require("request");

class API extends Component {

    static handleResponse(error, response, body, cb) {
        if (error) cb(error.toString(), 500);
        else if (response) {
            if (response.statusCode === 401) {
                App.authService.logout(body);
                let message = response.statusMessage;
                if (response.hasOwnProperty('data') && response['data'].hasOwnProperty('message')) message = body['data']['message'];
                cb(message, response.statusCode);
            }
            else if (response.statusCode === 200) {
                localStorage.setItem('auth_token', body['auth_token']);
                App.authService.authorizationHeader = body['auth_token'];
                cb(body['data'], response.statusCode);
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

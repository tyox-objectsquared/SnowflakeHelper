export class Query {
    constructor(execution_status, sql_text, username, error_code,
                error_message, start_time, end_time, total_elapsed_time) {
        this.execution_status = execution_status;
        this.sql_text = sql_text;
        this.username = username;
        this.error_code = error_code;
        this.error_message = error_message;
        this.start_time = start_time;
        this.end_time = end_time;
        this.total_elapsed_time = total_elapsed_time;
    }
}
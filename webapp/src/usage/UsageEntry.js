export class UsageEntry {
    constructor(warehouse_name: string, credits_used: number) {
        this.warehouse = warehouse_name;
        this.credits = credits_used;
    }
}
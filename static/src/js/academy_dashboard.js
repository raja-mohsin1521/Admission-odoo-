/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

class AcademyDashboard extends Component {
    setup() {
        this.state = useState({ 
            app: [], 
            voucher: [], 
            registers: [],
            total_stats: {},
            selectedRegister: 'all',
            selectedType: 'all'
        });
        this.appChartRef = useRef("appChart");
        this.voucherChartRef = useRef("voucherChart");
        this.actionService = useService("action");
        this.charts = {};

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this.loadData();
        });

        onMounted(() => {
            this.renderCharts();
        });
    }

    async loadData() {
        const data = await rpc("/academy/dashboard/stats", {
            register_id: this.state.selectedRegister,
            register_type: this.state.selectedType
        });
        this.state.app = data.app || [];
        this.state.voucher = data.voucher || [];
        this.state.registers = data.registers || [];
        this.state.total_stats = data.total_stats || {};
    }

    async onRegisterChange(ev) {
        this.state.selectedRegister = ev.target.value;
        await this.loadData();
        this.renderCharts();
    }

    async onTypeChange(ev) {
        this.state.selectedType = ev.target.value;
        await this.loadData();
        this.renderCharts();
    }

    renderCharts() {
        if (this.charts.app) this.charts.app.destroy();
        if (this.charts.voucher) this.charts.voucher.destroy();

        if (this.appChartRef.el) {
            this.charts.app = new Chart(this.appChartRef.el, {
                type: 'bar',
                data: {
                    labels: this.state.app.map(c => c.title),
                    datasets: [{
                        label: 'Applications',
                        data: this.state.app.map(c => c.value),
                        backgroundColor: 'rgba(54, 162, 235, 0.6)'
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        if (this.voucherChartRef.el) {
            this.charts.voucher = new Chart(this.voucherChartRef.el, {
                type: 'pie',
                data: {
                    labels: this.state.voucher.map(v => v.title),
                    datasets: [{
                        data: this.state.voucher.map(v => v.value),
                        backgroundColor: ['#4bc0c0', '#ffce56', '#ff6384', '#9966ff', '#ff9f40']
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }
    }

    async openFilter(field, value) {
        let domain = [[field, "=", value]];
        if (this.state.selectedRegister !== 'all') {
            domain.push(['register_id', '=', parseInt(this.state.selectedRegister)]);
        }
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "student.application",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }
}

AcademyDashboard.template = "odoo19_academy.academy_dashboard_template";
registry.category("actions").add("academy_dashboard_tag", AcademyDashboard);
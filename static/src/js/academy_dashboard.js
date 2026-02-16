/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

class AcademyDashboard extends Component {
    setup() {
        this.state = useState({ app: [], voucher: [] });
        this.appChartRef = useRef("appChart");
        this.voucherChartRef = useRef("voucherChart");
        this.actionService = useService("action");

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            const data = await rpc("/academy/dashboard/stats", {});
            this.state.app = data.app || [];
            this.state.voucher = data.voucher || [];
        });

        onMounted(() => {
            if (this.state.app.length || this.state.voucher.length) {
                this.renderCharts();
            }
        });
    }

    renderCharts() {
        if (this.appChartRef.el) {
            new Chart(this.appChartRef.el, {
                type: 'bar',
                data: {
                    labels: this.state.app.map(c => c.title),
                    datasets: [{
                        label: 'Applications',
                        data: this.state.app.map(c => c.value),
                        backgroundColor: 'rgba(54, 162, 235, 0.6)'
                    }]
                },
                options: { 
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        if (this.voucherChartRef.el) {
            new Chart(this.voucherChartRef.el, {
                type: 'pie',
                data: {
                    labels: this.state.voucher.map(v => v.title),
                    datasets: [{
                        data: this.state.voucher.map(v => v.value),
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.6)',
                            'rgba(255, 206, 86, 0.6)',
                            'rgba(255, 99, 132, 0.6)',
                            'rgba(153, 102, 255, 0.6)',
                            'rgba(255, 159, 64, 0.6)'
                        ]
                    }]
                },
                options: { 
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }

    async openFilter(field, value) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Filtered Applications",
            res_model: "student.application",
            domain: [[field, "=", value]],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }
}

AcademyDashboard.template = "odoo19_academy.academy_dashboard_template";
registry.category("actions").add("academy_dashboard_tag", AcademyDashboard);
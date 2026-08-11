// Alpine.js data component
document.addEventListener('alpine:init', () => {
    Alpine.data('screener', () => ({
        // State
        activeTab: 'stocks',
        stocks: [],
        fiis: [],
        loading: false,
        error: null,
        successMessage: null,
        lastUpdate: { stocks: null, fiis: null },
        sortColumn: 'score',
        sortDirection: 'desc',
        filtersExpanded: false,
        selectedMetric: null,

        // Stock filters (corrected from Excel analysis)
        stockFilters: {
            pl_min: 3,
            pl_max: 15,
            pvp_min: 0.7,
            pvp_max: 3,
            div_yield_min: 0.058,
            div_yield_max: 0.2,
            ev_ebit_min: 2.4,
            ev_ebit_max: 8.5,
            roic_min: 0.10,
            roic_max: null,
            roe_min: 0.06,
            roe_max: null,
            div_bruta_patrim_min: null,  // Allow negative (net cash = good)
            div_bruta_patrim_max: 2.5,
            cresc_rec_5a_min: 0.10,
            cresc_rec_5a_max: null,
        },

        // FII filters (default ranges from plan)
        fiiFilters: {
            dividend_yield_min: 0.06,
            dividend_yield_max: null,
            pvp_min: 0.80,
            pvp_max: 1.20,
            liquidez_min: 50000,
            liquidez_max: null,
            cap_rate_min: 0.07,
            cap_rate_max: null,
            vacancia_media_min: null,
            vacancia_media_max: 0.15,
        },

        // Computed
        get currentData() {
            return this.activeTab === 'stocks' ? this.stocks : this.fiis;
        },

        get currentFilters() {
            return this.activeTab === 'stocks' ? this.stockFilters : this.fiiFilters;
        },

        get currentLastUpdate() {
            return this.lastUpdate[this.activeTab];
        },

        // Init
        init() {
            this.loadData();
            this.fetchLastUpdate('stocks');
            this.fetchLastUpdate('fiis');

            // Debounced filter update
            this.$watch('stockFilters', () => {
                clearTimeout(this.filterTimeout);
                this.filterTimeout = setTimeout(() => this.loadData(), 300);
            });

            this.$watch('fiiFilters', () => {
                clearTimeout(this.filterTimeout);
                this.filterTimeout = setTimeout(() => this.loadData(), 300);
            });
        },

        // Methods
        switchTab(tab) {
            this.activeTab = tab;
            this.sortColumn = 'score';
            this.sortDirection = 'desc';
            this.loadData();
        },

        async loadData() {
            this.loading = true;
            this.error = null;

            try {
                const endpoint = this.activeTab === 'stocks' ? '/api/stocks' : '/api/fiis';
                const filters = this.currentFilters;

                // Build query params
                const params = new URLSearchParams();
                Object.entries(filters).forEach(([key, value]) => {
                    if (value !== null && value !== '') {
                        params.append(key, value);
                    }
                });

                const response = await fetch(`${endpoint}?${params}`);
                if (!response.ok) throw new Error('Failed to load data');

                const data = await response.json();

                if (this.activeTab === 'stocks') {
                    this.stocks = data;
                } else {
                    this.fiis = data;
                }

            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        async refreshData() {
            this.loading = true;
            this.error = null;
            this.successMessage = null;

            try {
                const response = await fetch(`/api/refresh?asset_type=${this.activeTab}`, {
                    method: 'POST'
                });

                if (response.status === 429) {
                    const data = await response.json();
                    this.error = data.detail;
                    return;
                }

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.detail || 'Refresh failed');
                }

                const result = await response.json();
                this.successMessage = result.message;

                // Reload data
                await this.loadData();
                await this.fetchLastUpdate(this.activeTab);

            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        async fetchLastUpdate(assetType) {
            try {
                const response = await fetch(`/api/last-update?asset_type=${assetType}`);
                if (!response.ok) return;

                const data = await response.json();
                this.lastUpdate[assetType] = data.last_updated_formatted;
            } catch (err) {
                console.error('Failed to fetch last update:', err);
            }
        },

        resetFilters() {
            if (this.activeTab === 'stocks') {
                this.stockFilters = {
                    pl_min: 0,
                    pl_max: 20,
                    pvp_min: 0,
                    pvp_max: 3,
                    div_yield_min: 0.05,
                    div_yield_max: 0.2,
                    ev_ebit_min: null,
                    ev_ebit_max: 10,
                    roic_min: 0.10,
                    roic_max: null,
                    div_bruta_patrim_min: null,
                    div_bruta_patrim_max: 3,
                    cresc_rec_5a_min: 0.10,
                    cresc_rec_5a_max: null,
                };
            } else {
                this.fiiFilters = {
                    dividend_yield_min: 0.06,
                    dividend_yield_max: null,
                    pvp_min: 0.80,
                    pvp_max: 1.20,
                    liquidez_min: 50000,
                    liquidez_max: null,
                    cap_rate_min: 0.07,
                    cap_rate_max: null,
                    vacancia_media_min: null,
                    vacancia_media_max: 0.15,
                };
            }
        },

        sort(column) {
            if (this.sortColumn === column) {
                this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortColumn = column;
                this.sortDirection = 'desc';
            }

            const data = this.activeTab === 'stocks' ? this.stocks : this.fiis;
            data.sort((a, b) => {
                const aVal = a[column] ?? -Infinity;
                const bVal = b[column] ?? -Infinity;

                if (this.sortDirection === 'asc') {
                    return aVal > bVal ? 1 : -1;
                } else {
                    return aVal < bVal ? 1 : -1;
                }
            });
        },

        formatNumber(value, decimals = 2) {
            if (value === null || value === undefined) return '-';
            return Number(value).toLocaleString('pt-BR', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            });
        },

        formatPercent(value) {
            if (value === null || value === undefined) return '-';
            return (value * 100).toLocaleString('pt-BR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }) + '%';
        },

        formatLarge(value) {
            if (value === null || value === undefined) return '-';
            if (value >= 1e9) {
                return (value / 1e9).toFixed(2) + 'B';
            }
            if (value >= 1e6) {
                return (value / 1e6).toFixed(2) + 'M';
            }
            if (value >= 1e3) {
                return (value / 1e3).toFixed(2) + 'K';
            }
            return value.toFixed(0);
        },

        scoreClass(score) {
            if (score >= 70) return 'score-high';
            if (score >= 40) return 'score-medium';
            return 'score-low';
        },

        sortClass(column) {
            if (this.sortColumn !== column) return 'sortable';
            return this.sortDirection === 'asc' ? 'sort-asc' : 'sort-desc';
        },

        toggleFilters() {
            this.filtersExpanded = !this.filtersExpanded;
        },

        isWinningMetric(stock, metric) {
            return stock.winning_metrics && stock.winning_metrics.includes(metric);
        },

        showMetricInfo(metricKey) {
            this.selectedMetric = this.getMetricInfo(metricKey);
        },

        closeMetricInfo() {
            this.selectedMetric = null;
        },

        exportCSV() {
            const data = this.currentData;
            if (!data.length) {
                alert('Nenhum dado para exportar');
                return;
            }

            // Build CSV content
            let csv = '';

            if (this.activeTab === 'stocks') {
                // Header
                csv = 'Score,Qualidade,Papel,Cotação,P/L,P/VP,Div.Yield,EV/EBIT,ROIC,ROE,Liq.2meses,Dív.L/P,Cresc.5a,Métricas Vencedoras\n';

                // Rows
                data.forEach(stock => {
                    const winners = (stock.winning_metrics || []).join(', ');
                    csv += [
                        stock.score || 0,
                        stock.quality_score ? stock.quality_score.toFixed(1) : '-',
                        stock.papel || '',
                        this.formatNumber(stock.cotacao),
                        this.formatNumber(stock.pl),
                        this.formatNumber(stock.pvp),
                        this.formatPercent(stock.div_yield),
                        this.formatNumber(stock.ev_ebit),
                        this.formatPercent(stock.roic),
                        this.formatPercent(stock.roe),
                        this.formatLarge(stock.liq_2meses),
                        this.formatNumber(stock.div_bruta_patrim),
                        this.formatPercent(stock.cresc_rec_5a),
                        winners
                    ].map(v => `"${v}"`).join(',') + '\n';
                });
            } else {
                // FII Header
                csv = 'Score,Qualidade,Papel,Segmento,Cotação,Div.Yield,FFO Yield,P/VP,Liquidez,Cap Rate,Vacância,Métricas Vencedoras\n';

                // Rows
                data.forEach(fii => {
                    const winners = (fii.winning_metrics || []).join(', ');
                    csv += [
                        fii.score || 0,
                        fii.quality_score ? fii.quality_score.toFixed(1) : '-',
                        fii.papel || '',
                        fii.segmento || '-',
                        this.formatNumber(fii.cotacao),
                        this.formatPercent(fii.dividend_yield),
                        this.formatPercent(fii.ffo_yield),
                        this.formatNumber(fii.pvp),
                        this.formatLarge(fii.liquidez),
                        this.formatPercent(fii.cap_rate),
                        this.formatPercent(fii.vacancia_media),
                        winners
                    ].map(v => `"${v}"`).join(',') + '\n';
                });
            }

            // Generate filename with timestamp
            const now = new Date();
            const timestamp = now.toISOString().slice(0,16).replace('T', '_').replace(/:/g, 'h');
            const assetType = this.activeTab === 'stocks' ? 'acoes' : 'fiis';
            const filename = `${assetType}_${timestamp}.csv`;

            // Create download link
            const BOM = '﻿'; // UTF-8 BOM for Excel
            const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();
        },

        getMetricInfo(key) {
            const stockMetrics = {
                score: {
                    name: 'Score & Qualidade',
                    description: 'Score (número grande) = quantas métricas a ação vence (0-8 pontos). Q (número pequeno) = qualidade geral (0-100), calculada como média dos percentis em todas as métricas. Ordenação: primeiro por Score, depois por Qualidade para desempate. Exemplo: Score 2 | Q: 79.2 = vence 2 métricas, qualidade geral muito boa.',
                    filters: null
                },
                pl: {
                    name: 'P/L (Preço/Lucro)',
                    description: 'Mede quantos anos de lucro são necessários para pagar o preço da ação. P/L baixo pode indicar subvalorização. Empresas com prejuízo têm P/L negativo (não aparece nos filtros).',
                    filters: this.stockFilters.pl_min || this.stockFilters.pl_max ?
                        `${this.stockFilters.pl_min || '-∞'} a ${this.stockFilters.pl_max || '+∞'}` : null
                },
                pvp: {
                    name: 'P/VP (Preço/Valor Patrimonial)',
                    description: 'Compara o preço de mercado com o valor contábil da empresa. P/VP < 1 sugere negociação abaixo do valor patrimonial. P/VP muito baixo pode indicar problemas estruturais.',
                    filters: this.stockFilters.pvp_min || this.stockFilters.pvp_max ?
                        `${this.stockFilters.pvp_min || '-∞'} a ${this.stockFilters.pvp_max || '+∞'}` : null
                },
                div_yield: {
                    name: 'Dividend Yield',
                    description: 'Percentual de dividendos pagos em relação ao preço da ação (anualizado). Yield alto indica boa distribuição de lucros aos acionistas. Empresas em crescimento costumam ter yield menor.',
                    filters: this.stockFilters.div_yield_min || this.stockFilters.div_yield_max ?
                        `${this.formatPercent(this.stockFilters.div_yield_min)} a ${this.formatPercent(this.stockFilters.div_yield_max) || '+∞'}` : null
                },
                ev_ebit: {
                    name: 'EV/EBIT',
                    description: 'Enterprise Value sobre EBIT (lucro operacional). Mede quantos anos de lucro operacional são necessários para pagar o valor total da empresa (incluindo dívidas). Valores baixos (< 10) indicam boa relação preço/lucro operacional.',
                    filters: this.stockFilters.ev_ebit_min || this.stockFilters.ev_ebit_max ?
                        `${this.stockFilters.ev_ebit_min || '-∞'} a ${this.stockFilters.ev_ebit_max || '+∞'}` : null
                },
                roic: {
                    name: 'ROIC (Retorno sobre Capital Investido)',
                    description: 'Eficiência da empresa em gerar lucro com o capital alocado (próprio + terceiros). ROIC > 10% indica boa gestão e vantagem competitiva. ROIC > custo de capital = geração de valor.',
                    filters: this.stockFilters.roic_min || this.stockFilters.roic_max ?
                        `${this.formatPercent(this.stockFilters.roic_min)} a ${this.formatPercent(this.stockFilters.roic_max) || '+∞'}` : null
                },
                roe: {
                    name: 'ROE (Retorno sobre Patrimônio Líquido)',
                    description: 'Rentabilidade do capital dos acionistas. ROE alto (> 15%) indica empresa lucrativa. Atenção: ROE pode ser inflado por alta alavancagem (muita dívida).',
                    filters: this.stockFilters.roe_min || this.stockFilters.roe_max ?
                        `${this.formatPercent(this.stockFilters.roe_min)} a ${this.formatPercent(this.stockFilters.roe_max) || '+∞'}` : null
                },
                div_bruta_patrim: {
                    name: 'Dívida Líquida / Patrimônio',
                    description: 'Nível de endividamento líquido (dívida bruta menos caixa). Valores negativos = empresa tem mais caixa que dívida (bom). < 1 é saudável, > 3 pode ser arriscado. Empresas cíclicas toleram mais dívida.',
                    filters: this.stockFilters.div_bruta_patrim_min !== null || this.stockFilters.div_bruta_patrim_max ?
                        `${this.stockFilters.div_bruta_patrim_min !== null ? this.stockFilters.div_bruta_patrim_min : '-∞'} a ${this.stockFilters.div_bruta_patrim_max || '+∞'}` : null
                },
                cresc_rec_5a: {
                    name: 'Crescimento de Receita (5 anos)',
                    description: 'Taxa de crescimento anual composto (CAGR) da receita nos últimos 5 anos. > 10% indica empresa em expansão. Crescimento muito alto pode ser insustentável ou vir de aquisições.',
                    filters: this.stockFilters.cresc_rec_5a_min || this.stockFilters.cresc_rec_5a_max ?
                        `${this.formatPercent(this.stockFilters.cresc_rec_5a_min)} a ${this.formatPercent(this.stockFilters.cresc_rec_5a_max) || '+∞'}` : null
                }
            };

            const fiiMetrics = {
                score: {
                    name: 'Score & Qualidade',
                    description: 'Score (número grande) = quantas métricas o FII vence (0-6 pontos): maior Div.Yield, maior FFO Yield, P/VP mais próximo de 1.0, maior Liquidez, maior Cap Rate, menor Vacância. Q (número pequeno) = qualidade geral (0-100). Ordenação: primeiro por Score, depois por Qualidade.',
                    filters: null
                },
                dividend_yield: {
                    name: 'Dividend Yield',
                    description: 'Dividendos anuais divididos pelo preço da cota. Mostra retorno de renda passiva. FIIs de qualidade normalmente pagam > 6% ao ano. Yield muito alto pode indicar risco (vacância, inadimplência).',
                    filters: this.fiiFilters.dividend_yield_min || this.fiiFilters.dividend_yield_max ?
                        `${this.formatPercent(this.fiiFilters.dividend_yield_min)} a ${this.formatPercent(this.fiiFilters.dividend_yield_max) || '+∞'}` : null
                },
                pvp: {
                    name: 'P/VP (Preço/Valor Patrimonial)',
                    description: 'Compara cotação com valor dos imóveis (NAV). P/VP próximo de 1.0 indica negociação justa. P/VP < 0.9 = desconto, P/VP > 1.1 = prêmio. Fundos de papel toleram mais volatilidade.',
                    filters: this.fiiFilters.pvp_min || this.fiiFilters.pvp_max ?
                        `${this.fiiFilters.pvp_min || '-∞'} a ${this.fiiFilters.pvp_max || '+∞'}` : null
                },
                liquidez: {
                    name: 'Liquidez Diária',
                    description: 'Volume financeiro negociado por dia (em R$). Mínimo recomendado: R$ 50.000 para facilitar compra/venda sem grande impacto no preço. FIIs ilíquidos têm spread alto.',
                    filters: this.fiiFilters.liquidez_min || this.fiiFilters.liquidez_max ?
                        `R$ ${this.formatLarge(this.fiiFilters.liquidez_min)} a ${this.fiiFilters.liquidez_max ? this.formatLarge(this.fiiFilters.liquidez_max) : '+∞'}` : null
                },
                cap_rate: {
                    name: 'Cap Rate (Taxa de Capitalização)',
                    description: 'Retorno anual dos imóveis (NOI / valor dos imóveis). Indica qualidade operacional dos ativos. Cap Rate > 7% é bom. Compare com taxa Selic para avaliar atratividade vs renda fixa.',
                    filters: this.fiiFilters.cap_rate_min || this.fiiFilters.cap_rate_max ?
                        `${this.formatPercent(this.fiiFilters.cap_rate_min)} a ${this.formatPercent(this.fiiFilters.cap_rate_max) || '+∞'}` : null
                },
                vacancia_media: {
                    name: 'Vacância Média',
                    description: 'Percentual de área vazia (sem inquilinos). Menor = mais estável. Vacância > 15% é sinal de alerta (pode haver corte de dividendos). Shoppings toleram até 5-8%, logística 0-3%.',
                    filters: this.fiiFilters.vacancia_media_min !== null || this.fiiFilters.vacancia_media_max ?
                        `${this.fiiFilters.vacancia_media_min !== null ? this.formatPercent(this.fiiFilters.vacancia_media_min) : '0%'} a ${this.formatPercent(this.fiiFilters.vacancia_media_max) || '+∞'}` : null
                }
            };

            const metrics = this.activeTab === 'stocks' ? stockMetrics : fiiMetrics;
            return metrics[key] || null;
        }
    }));
});

def gross_cents(net_cents, rates, country="DE"):
    percent = rates.percent(country)
    return (net_cents * (100 + percent) + 50) // 100

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random, string

app = Flask(__name__)
app.secret_key = 'MasterTaxTechnology'


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'verkoop_transacties' not in session:
        session['verkoop_transacties'] = []
    result = None
    aantal_jaren = '0'
    transacties = session.get('transacties', [])
    verkoop_transacties = session.get('verkoop_transacties', []) # nieuwe regel
    if request.method == 'POST':
        transactie_type = request.form.get('transactie_type')
        transactie_bedrag = float(request.form.get('transactie_bedrag'))
        
        if transactie_type in ['Onttrekking', 'Storting']:
            result = f"{transactie_bedrag:.2f}"
            mededeling = '11;' + result if transactie_type == 'Onttrekking' else '10;' + result  # 11 voor onttrekkingen en 10 voor stortingen
            transactie = {
                'btw_id': 'NL' + ''.join(random.choices(string.digits, k=12)) + 'B' + ''.join(random.choices(string.digits, k=2)),
                'btw_percentage': 'N/A',
                'exclusief_btw': "{:.2f}".format(transactie_bedrag),
                'restwaarde': 0,
                'afschrijvingstermijn': 0,
                'mededeling': mededeling,
                'jaarlijkse_afschrijving': "{:.2f}".format(0),
            }
            if transactie_type == 'Onttrekking':
                transacties.append(transactie)
            else:  # Storting
                session['verkoop_transacties'].append(transactie)
            session['transacties'] = transacties
            session['verkoop_transacties'] = verkoop_transacties # nieuwe regel
            session['laatste_transactie'] = transactie
            return redirect(url_for('index'))

        btw_percentage = request.form.get('btw_percentage')
        def select(btw_percentage):
            options = {"Vrijgesteld": "99", "0%": "00", "9%": "09", "21%": "21"}
            if btw_percentage in options:
                return options[btw_percentage]
            else:
                return None

        # Controleer of btw_percentage een geldige waarde heeft
        btw_conversion = {"Vrijgesteld": 0.00, "0%": 0.00, "9%": 0.09, "21%": 0.21}.get(btw_percentage)

        if btw_conversion is not None:
            # Voeg 1 toe aan het btw_percentage om de berekening correct uit te voeren
            exclusief_btw = transactie_bedrag / (1 + btw_conversion)
            output_btw_percentage = select(btw_percentage)

            if transactie_type == 'aankoop_zonder_afschrijving':
                result = f"{output_btw_percentage};{exclusief_btw:.2f};0;0"
            elif transactie_type == 'aankoop_met_afschrijving':
                restwaarde = request.form.get('restwaarde', '0')
                aantal_jaren = request.form.get('aantal_jaren', '0')
                result = f"{output_btw_percentage};{exclusief_btw:.2f};{restwaarde};{aantal_jaren}"

        if result:
            jaarlijkse_afschrijving = (float(exclusief_btw)-float(restwaarde)) / float(aantal_jaren) if aantal_jaren != '0' else 0
            transacties.append({
                'btw_id': 'NL' + ''.join(random.choices(string.digits, k=12)) + 'B' + ''.join(random.choices(string.digits, k=2)),
                'btw_percentage': btw_percentage,
                'exclusief_btw': "{:.2f}".format(exclusief_btw),
                'restwaarde': restwaarde if transactie_type == 'aankoop_met_afschrijving' else '0',
                'afschrijvingstermijn': aantal_jaren if transactie_type == 'aankoop_met_afschrijving' else '0',
                'mededeling': result,
                'jaarlijkse_afschrijving': "{:.2f}".format(jaarlijkse_afschrijving),
            })
            session['transacties'] = transacties
            session['laatste_transactie'] = transacties[-1]
            return redirect(url_for('index'))

    return render_template('index.html', result=result, laatste_transactie=session.get('laatste_transactie'), transacties=transacties, laatste_verkoop=session.get('laatste_verkoop'), verkoop_transacties=session.get('verkoop_transacties', []))


@app.route('/verkoop', methods=['POST'])
def verkoop():
    if 'verkoop_transacties' not in session:
        session['verkoop_transacties'] = []
    aantal_jaren = '0'
    restwaarde = '0'
    result = None
    verkoop_transacties = session.get('verkoop_transacties', [])

    if request.method == 'POST':
        verkoop_type = request.form.get('verkoop_type')
        verkoop_bedrag = float(request.form.get('verkoop_bedrag'))

        if verkoop_type != 'storting':
            btw_percentage = request.form.get('verkoop_btw_percentage')
            def select(btw_percentage):
                options = {"Vrijgesteld": "99", "0%": "00", "9%": "09", "21%": "21"}
                if btw_percentage in options:
                    return options[btw_percentage]
                else:
                    return None
            btw_conversion = {"Vrijgesteld": 0.00, "0%": 0.00, "9%": 0.09, "21%": 0.21}.get(btw_percentage)
            exclusief_btw = verkoop_bedrag / (1 + btw_conversion)
            output_btw_percentage = select(btw_percentage)
        else:
            btw_percentage = 'N/A'
            btw_conversion = 'N/A'
            exclusief_btw = verkoop_bedrag
            output_btw_percentage = '10'

        if verkoop_type == 'verkoop_zonder_afschrijving':
            result = f"{output_btw_percentage};{exclusief_btw:.2f};0;0"
        elif verkoop_type == 'verkoop_met_afschrijving':
            restwaarde = request.form.get('verkoop_restwaarde', '0')
            aantal_jaren = request.form.get('verkoop_aantal_jaren', '0')
            result = f"{output_btw_percentage};{exclusief_btw:.2f};{restwaarde};{aantal_jaren}"
        elif verkoop_type == 'storting':
            result = f"10;{exclusief_btw:.2f};0;0"

        if result:
            jaarlijkse_afschrijving = (float(exclusief_btw)-float(restwaarde)) / float(aantal_jaren) if aantal_jaren != '0' else 0
            verkoop_transacties.append({
                'btw_id': 'NL' + ''.join(random.choices(string.digits, k=12)) + 'B' + ''.join(random.choices(string.digits, k=2)),
                'btw_percentage': btw_percentage,
                'exclusief_btw': "{:.2f}".format(exclusief_btw),
                'restwaarde': restwaarde if verkoop_type == 'verkoop_met_afschrijving' else '0',
                'afschrijvingstermijn': aantal_jaren if verkoop_type == 'verkoop_met_afschrijving' else '0',
                'mededeling': result,
                'jaarlijkse_afschrijving': "{:.2f}".format(jaarlijkse_afschrijving),
            })
            session['verkoop_transacties'] = verkoop_transacties
            session['laatste_verkoop'] = verkoop_transacties[-1]

        return redirect(url_for('index'))


    
@app.route('/vooringevulde_aangifte', methods=['GET', 'POST'])
def vooringevulde_aangifte():
    transacties = session.get('transacties', [])
    verkoop_transacties = session.get('verkoop_transacties', [])
    innovatiebox = session.get('innovatiebox', 0)

    totale_inkomsten = sum(float(verkoop['exclusief_btw']) for verkoop in session['verkoop_transacties'] if not verkoop['mededeling'].startswith(('10', '11')))
    totale_uitgaven = sum(float(aankoop['jaarlijkse_afschrijving']) if float(aankoop['jaarlijkse_afschrijving']) > 0 else float(aankoop['exclusief_btw']) for aankoop in session['transacties'] if not aankoop['mededeling'].startswith(('10', '11')))

    totale_waarde_onttrekkingen = sum(float(transactie['exclusief_btw']) for transactie in transacties if transactie['mededeling'].startswith('11'))  # Nieuwe regel
    totale_waarde_stortingen = sum(float(transactie['exclusief_btw']) for transactie in verkoop_transacties if transactie['mededeling'].startswith('10'))

    saldo = totale_inkomsten - totale_uitgaven  # Define saldo here
    belastbaar_bedrag = saldo 

    session['totale_inkomsten'] = totale_inkomsten
    session['totale_uitgaven'] = totale_uitgaven
    session['saldo'] = saldo  # You can also store saldo in the session if needed
    session['totale_waarde_onttrekkingen'] = totale_waarde_onttrekkingen  # Nieuwe regel
    session['totale_waarde_stortingen'] = totale_waarde_stortingen

    return render_template('vooringevulde_aangifte.html', 
                           totale_inkomsten=session.get('totale_inkomsten', 0), 
                           totale_uitgaven=session.get('totale_uitgaven', 0),
                           totale_waarde_onttrekkingen=session.get('totale_waarde_onttrekkingen', 0),
                           totale_waarde_stortingen=session.get('totale_waarde_stortingen', 0),
                           saldo=session.get('saldo', 0), 
                           innovatiebox=innovatiebox,
                           deelnemingsvrijstelling=0, 
                           renteaftrekbeperkingen=0, 
                           afwaarderingen=0, 
                           verrekenbare_verliezen=0, 
                           reserves=0,
                           belastbaar_bedrag=belastbaar_bedrag)

@app.route('/verberg_vooringevulde_aangifte', methods=['GET', 'POST'])
def verberg_vooringevulde_aangifte():
    session.pop('totale_inkomsten', None)
    session.pop('totale_uitgaven', None)
    return redirect(url_for('index'))
    pass


if __name__ == '__main__':
    app.run(debug=True)

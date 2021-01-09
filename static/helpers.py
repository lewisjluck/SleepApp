class Client :
    #Initialise a client with appropriate details
    def __init__(self, first_name, last_name, dva_num, address, suburb, state, postcode, number):
        self.first_name = first_name
        self.last_name = last_name
        self.dva_num = dva_num
        self.address = address
        self.suburb = suburb
        self.state = state
        self.postcode = postcode
        self.number = number

class Product:
    #Initialise a product with appropriate details
    def __init__(self, reference, lot, quantity, description):
        self.reference = reference
        self.lot = lot
        self.quantity = quantity
        self.description = description

class Form:
    #Initialise a form with a Client, pages of Products, and options
    def __init__(self, client, products, options, new):
        #Assign main details to values
        self.new = new
        self.client = client
        self.details = [
        client.dva_num,
        client.first_name[0],
        client.last_name,
        client.suburb,
        client.state,
        client.postcode,
        ""]

        #Product codes for frequent service products
        SERVICE_PRODUCTS = {
            "report": Product("REPORT-PAP", "SERVICE CLINICAL", "1", "PAP COMPLIANCE DOWNLOAD REPORT"),
            "visit": Product("VISIT-PAP", "SERVICE CLINICAL", "1", "PAP CONSULTATION"),
            "delivery": Product(self.find_distance(), "SERVICE TRAVEL", "1", "DELIVERY"),
            "setup": Product("SETUP-PAP", "SERVICE CLINICAL", "1", "PAP INITIAL SETUP AND 2 X FOLLOW UP"),
            "urgent": Product("URGENT-PAP", "SERVICE CLINICAL", "1", "URGENT DELIVERY")
        }

        #Format address appropriately across the three fields
        addresses = [client.address, "", ""]
        for (i, address) in enumerate(addresses):
            if len(address) > 25:
                for j in range(len(address.split())):
                    new = " ".join(address.split()[:-(j+1)])
                    if len(new) < 25 and not new == address:
                        addresses[i] = new
                        addresses[i+1] = " ".join(address.split()[-j-1:])
                        break
        self.details[3:3] = addresses

        pages = [[]]
        i = 0

        #Populate "pages" with products, keeping services together on the same page
        while products:
            pages[i].append(products.pop(0))
            if not products:
                page_options = []
                for option, setting in options.items():
                    if setting:
                        page_options.append(SERVICE_PRODUCTS[option])
                if (len(pages[i]) + len(options)) > 5:
                    pages.append(page_options)
                else:
                    pages[i] += options
                break
            if len(pages[i]) == 5:
                pages.append([])
                i += 1

        #Assign values
        self.pages = pages

    def find_distance(self):
        #Import API libaries
        import googlemaps

        #Open file for secret
        secret = open("secret.txt", "r").readlines()

        #Work address
        WORK_ADDRESS = secret[3]

        #Google maps API key
        GOOGLE_MAPS_API_KEY = secret[4]

        #Find distance between origin and form address using Google Maps API
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        distances = gmaps.distance_matrix(WORK_ADDRESS, self.client.address + self.client.suburb + self.client.state)

        #Try to use distance to output appropriate reference
        try:
            dist = distances["rows"][0]["elements"][0]["distance"]["value"] * 2
            if dist < 50000:
                distance = 50
            elif dist >= 50000 and dist < 100000:
                distance = 100
            elif dist >= 100000 and dist < 200000:
                distance = 200
            elif dist >=200000:
                distance = 201

            return str(distance) + "DIST"

        #If address is not found, will return reference of "ERROR" and print an error message
        except:
            print("Location not found, as per matrix: \n", distances)
            return "ERROR"

    def make_pdf(self):
        #Import dependencies
        from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
        from PyPDF2.generic import NameObject, BooleanObject, IndirectObject
        from datetime import date
        import os
        import pypdftk

        pdf_pages = []

        #Cycle through pages
        for j, page in enumerate(self.pages):

            template_name = "static/pdf_templates/form.pdf"

            #Read pdf templates using PyPDF2
            form = PdfFileReader(open(template_name, "rb"))

            #Get main form field names from pdf reader
            fields = form.getFields(tree=None, retval=None, fileobj=None)
            field_names = list(fields.keys())

            #PDF writers using PyPDF2
            writer = PdfFileWriter()

            #Make a copy of field_values
            field_values = self.details[:]

            #Add values from each page
            for product in page:
                field_values += [product.reference, product.lot, product.quantity, product.description]

            #Pad out unused fields, zip into dict for writing
            field_values += [""] * (len(field_names) - len(field_values))
            field_dict = dict(zip(field_names, map(lambda x:x.upper(), field_values)))
            print(field_dict)

            #Add page to writer, update fields from input data
            pdf_pages.append(pypdftk.fill_form(template_name, field_dict))

            """
            page = form.getPage(0)
            writer.addPage(form.getPage(0))
            writer.updatePageFormFieldValues(writer.getPage(0), field_dict)

            #Set form fields to visible
            if "/AcroForm" not in writer._root_object:
                writer._root_object.update({NameObject("/AcroForm"): IndirectObject(len(writer._objects), 0, writer)})
            writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

            #Write pdf to file
            with open("print" + str(j) + ".pdf", "wb") as output:
                writer.write(output)
            """


        end_form_template_name = "static/pdf_templates/end_page.pdf"
        #Get pdf templates using PyPDF2
        end_form = PdfFileReader(open(end_form_template_name, "rb"))

        #Get end form fields from reader
        end_fields = end_form.getFields(tree=None, retval=None, fileobj=None)
        end_field_names = list(end_fields.keys())

        #Populate end field values with name and date, position depending on options
        end_field_values = [""] * 4
        index = 2 if self.new else 0
        current_date = date.today()
        end_field_values[index:index+1] = [self.client.first_name + " " + self.client.last_name, current_date.strftime("%d/%m/%Y")]

        #Zip end field values and names into dict
        end_field_dict = dict(zip(end_field_names, end_field_values))

        pdf_pages.append(pypdftk.fill_form(end_form_template_name, end_field_dict))
        pypdftk.concat(pdf_pages, "print.pdf")

        """
        writer = PdfFileWriter()

        #Fill and add end page to writer
        writer.addPage(end_form.getPage(0))
        writer.updatePageFormFieldValues(writer.getPage(0), end_field_dict)

        #Set form fields to visible
        if "/AcroForm" not in writer._root_object:
            writer._root_object.update({NameObject("/AcroForm"): IndirectObject(len(writer._objects), 0, writer)})
        writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

        #Write pdf to file
        with open("print" + str(len(self.pages)) + ".pdf", "wb") as output:
            writer.write(output)
        """
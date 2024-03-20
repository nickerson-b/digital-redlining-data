# converter class
class AddressConverter:
    def __init__(self, company_formatting: str):
        self.company_formatting = company_formatting

    # convert a list of addresses into centurylink format
    # accepts a list of addresses in raw (usps) form
    # returns a list of addresses in centurylink format
    def cl_list_converter(self, addresses_raw: list):
        cleaned_addresses = []
        for address in addresses_raw:
            props = address['properties']
            cleaned_addresses.append((props['number'] + " " + props['street'] + " SEATTLE WA " + props['zip'] + " USA"))
        return cleaned_addresses
    
    # figure out what converter is running and call the proper list converter
    # adding more company formats should be easy
    def list_converter(self, addresses_raw: list):
        if not isinstance(addresses_raw, list):
            raise TypeError('Not a list')
        if self.company_formatting == 'cl':
            return self.cl_list_converter(addresses_raw=addresses_raw)
        return -1
        
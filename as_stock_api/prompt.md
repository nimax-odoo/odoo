<specs>  
- **Objective:** Develop a REST API endpoint in Odoo 17 to expose stock availability in a read-only manner.  
- **Method:** The API should use `GET` requests.  
- **Route:** `/nimax/stock`  
- **Model:** `stock.quant` (to retrieve stock data).  
- **Filters:**  
  - `product_id` (optional) → Filter stock for a specific product.  
  - `location_id` (optional) → Filter stock by warehouse/location.  
- **Security:**  
  - Authentication required (`auth='user'` for Odoo users or API key validation).  
  - Only users with read permissions in `stock.quant` should have access.  
- **Response Format:** JSON with the following fields:  
  - `product_id`: Product identifier.  
  - `product_name`: Product name.  
  - `available_qty`: Available stock quantity.  
  - `location_id`: Warehouse or location ID.  
  - `location_name`: Name of the warehouse/location.  
  - `last_update`: Last update timestamp.  
- **Performance Considerations:**  
  - Optimize queries to avoid unnecessary database load.  
  - Fetch only required fields.  
  - Implement caching if needed.  
- **Security Considerations:**  
  - Ensure the API does not allow stock modifications.  
  - CSRF protection must be disabled for API requests.  
  - API key validation should be used if `auth='none'` is selected.  
</specs>  

<your_task>  
1. Create an Odoo controller in `controllers/main.py` to handle the API request.  
2. Define a `GET` route at `/nimax/stock` using `@http.route`.  
3. Implement authentication and validate user permissions.  
4. Query `stock.quant` and filter results based on `product_id` and `location_id`.  
5. Construct the JSON response, including all required fields.  
6. Ensure the endpoint does not allow stock modifications.  
7. Implement API key authentication if `auth='none'` is used.  
8. Optimize query execution to minimize database load.  
9. Implement error handling:  
   - Return `403` for unauthorized access.  
   - Return `400` for invalid parameters.  
   - Return `200` for successful responses.  
</your_task>  

<rules>
- Odoo 15 enterprise
- Developer is: Ahorasoft.com
- syntax:
  - For variables, classes and functions, filenames, use 'as_' as prefix
  - comment all the code in spanish, with examples
- Crea el ChangeLog.txt y el README.md
- the module name is as_stock_api, and all code must be inside in as_stock_api
- Don't touch other modules
- The API must be **read-only**; no write operations should be allowed.  
- Authentication is mandatory (`auth='user'` or API key).  
- Queries must be **optimized**, avoiding unnecessary fields or joins.  
- Response data must follow the **JSON structure** defined in `<specs>`.  
- Errors must return **proper HTTP status codes** (`400`, `403`, `200`).  
- CSRF protection should be **disabled** for API requests.  
- The API key (if used) must be stored securely in `ir.config_parameter`.
</rules>
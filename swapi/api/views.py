import json

from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from api.models import Planet, People
from api.fixtures import SINGLE_PEOPLE_OBJECT, PEOPLE_OBJECTS
from api.serializers import serialize_people_as_json


def single_people(request):
    return JsonResponse(SINGLE_PEOPLE_OBJECT)


def list_people(request):
    return JsonResponse(PEOPLE_OBJECTS, safe=False)


@csrf_exempt
def people_list_view(request):
    """
    People `list` actions:

    Based on the request method, perform the following actions:

        * GET: Return the list of all `People` objects in the database.

        * POST: Create a new `People` object using the submitted JSON payload.

    Make sure you add at least these validations:

        * If the view receives another HTTP method out of the ones listed
          above, return a `400` response.

        * If submited payload is nos JSON valid, return a `400` response.
    """
    if request.body:
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except ValueError:
            return JsonResponse(
                {"success": False, "msg": "Provide a valid JSON payload"},
                status=400)
        status = 200
        
    if request.method == 'GET':
        qs = People.objects.all()
        data = [serialize_people_as_json(people) for people in qs]
        status = 201
        
    elif request.method == 'POST':
        planet_id = payload.get('homeworld', None)
        try:
            planet = Planet.objects.get(id=planet_id)
        except Planet.DoesNotExist:
            return JsonResponse(
                {"success": False, "msg": "Could not find planet with id: {}".format(planet_id)},
                status=404)
        try:
            people = People.objects.create(
                name=payload['name'],
                homeworld=planet,
                height=payload['height'],
                mass=payload['mass'],
                hair_color=payload['hair_color'])
        except (ValueError, KeyError):
            return JsonResponse(
                {"success": False, "msg": "Provided payload is not valid"},
                status=400)
        data = serialize_people_as_json(people)
        status = 201
        
    else:
        data = {"success": False, "msg": "Invalid HTTP method"}
        status=400
        
    return JsonResponse(data, status=status, safe=False)
    
@csrf_exempt
def people_detail_view(request, people_id):
    """
    People `detail` actions:

    Based on the request method, perform the following actions:

        * GET: Returns the `People` object with given `people_id`.

        * PUT/PATCH: Updates the `People` object either partially (PATCH)
          or completely (PUT) using the submitted JSON payload.

        * DELETE: Deletes `People` object with given `people_id`.

    Make sure you add at least these validations:

        * If the view receives another HTTP method out of the ones listed
          above, return a `400` response.

        * If submited payload is nos JSON valid, return a `400` response.
    """
    try:
        people = People.objects.get(id=people_id)
    except people.DoesNotExist:
        return JsonResponse(
                {"success": False, "msg": "Could not find people with id: {}".format(people_id)},
                status=404)
        
    if request.body:
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except ValueError:
            return JsonResponse(
                {"success": False, "msg": "Provide a valid JSON payload"},
                status=400)
        status = 200
        
    if request.method == 'GET':
        
        data = serialize_people_as_json(people)
        status = 200
        
    elif request.method in ['PUT', 'PATCH']:
        for field in ['name', 'homeworld', 'mass', 'height', 'hair_color']:
            if not field in payload:
                if request.method == 'PATCH':
                    continue
                return JsonResponse(
                    {"success": False, "msg": "Missing field in full update"},
                    status=400)
            if field == 'homeworld':
                try:
                    payload['homeworld'] = Planet.objects.get(id=payload['homeworld'])
                except Planet.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "msg": "Could not find planet with id: {}".format(payload['homeworld'])},
                        status=404)
            try:
                setattr(people, field, payload[field]) #instance,attribute,value
                people.save()
            except ValueError:
                return JsonResponse(
                    {"success": False, "msg": "Provided payload is not valid"},
                    status=400)
        data = serialize_people_as_json(people)
    elif request.method == 'DELETE':
        # DELETE /people/:id
        people.delete()
        data = {"success": True}
    else:
        data = {"success": False, "msg": "Invalid HTTP method"}
        status=400
                
        
    return JsonResponse(data, safe=False, status=status)
    
@method_decorator(csrf_exempt, name='dispatch') 
#same as doing inside the class
# def dispatch(self, request, *arg, **kwargs):
#     return super().dispatch(self, request, *arg, **kwargs)
class PeopleView(View):
    
    def _get_object(self, people_id):
        try:
            return People.objects.get(id=people_id)
        except People.DoesNotExist:
            return None
            
    def get(self, *arg, **kwargs):
        people_id = kwargs.get('people_id')
        if people_id:
            people = self._get_object(people_id)
            if not people:
                return JsonResponse(
                    {"success": False, "msg":"Could not find people with id: {}".format(people_id)}, status=404)
            data = serialize_people_as_json(people)
        else:
            qs = People.objects.select_related('homeworld').all()
            data = [serialize_people_as_json(people) for people in qs]
        return JsonResponse(data, status=200, safe=False)
        
    def post(self, *arg, **kwargs):
        if 'people_id' in kwargs:
            return JsonResponse(
                {"success":False, "msg":"Invalid HTTP request"}, status=400)
                
        try:
            payload = json.loads(self.request.body.decode('utf-8'))
        except ValueError:
            return JsonResponse(
                {"success":False, "msg":"Provide a valid JSON payload"}, status=400)
        
        planet_id = payload.get('homeworld', None)
        try:
            planet = Planet.objects.get(id=planet_id)
            # we can do payload['homeworld'] = Planet.objects.get(id=planet_id)
            # and pass **payload to People.objects.create(**payload)
        except Planet.DoesNotExist:
            return JsonResponse(
            {"success":False, "msg":"Could not find planet with id {}".format(planet_id)}, status=404)
            
        try:
            people = People.objects.create(
                name=payload['name'],
                homeworld=planet,
                height=payload['height'],
                mass=payload['mass'],
                hair_color=payload['hair_color'])
        except (ValueError,KeyError):
            return JsonResponse(
                {"success": False, "msg":"Provided payload is not valid"}, status=400)
        
        data=serialize_people_as_json(people)
        return JsonResponse(data, status=201, safe=False)
        
    def delete(self, *arg, **kwargs):
        if not 'people_id' in kwargs:
            return JsonResponse(
                {"success":False, "msg":"Invalid HTTP request"}, status=400)
        people_id = kwargs.get('people_id')     
        people = self._get_object(people_id)
        if not people:
            return JsonResponse(
                {"success": False, "msg":"Could not find people with id {}".format(people_id)}, status=404)
        data = {"success": True}
        people.delete()
        return JsonResponse
        
        
    def _update(self, people, payload, partial=False):
        for field in ['name', 'homeworld', 'mass', 'height', 'hair_color']:
            if not field in payload:
                if partial:
                    continue
                return JsonResponse(
                    {"success": False, "msg":"Missing field in full update"}, status=400)
            if field == 'homeworld':
                try:
                    payload['homeworld'] = Planet.objects.get(id=payload['homeworld'])
                except Planet.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "msg":"Planet with id {} does not exist".format(payload['homeworld'])}, status=400)
                
            try:
                setattr(people, field, payload[field])
                people.save()
            except ValueError:
                return JsonResponse(
                    {"success": False, "msg":"Provided Json is not valid"}, status=400)
        data = serialize_people_as_json(people)
        return JsonResponse(data, status=200, safe=False)
                    

    def patch(self, *arg, **kwargs):
        people_id = kwargs.get('people_id')
        people = self._get_object(people_id)
        if not people:
            return JsonResponse(
                {"success": False, "msg":"Could not find people with id {}".format(people_id)}, status=404)
        try:        
            payload = json.loads(self.request.body.decode('utf-8'))
        except ValueError:
            return JsonResponse({"success": False, "msg":"Provided payload is not valid"}, status=400)
        return self._update(people, payload, partial=True)
        
    def put(self, *arg, **kwargs):
        people_id = kwargs.get('people_id')
        people = self._get_object(people_id)
        if not people:
            return JsonResponse(
                {"success": False, "msg":"Could not find people with id {}".format(people_id)}, status=404)
        try:        
            payload = json.loads(self.request.body.decode('utf-8'))
        except ValueError:
            return JsonResponse({"success": False, "msg":"Provided payload is not valid"}, status=400)
        return self._update(people, payload, partial=False)
        